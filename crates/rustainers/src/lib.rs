extern crate tar;

use bollard::container::{Config, CreateContainerOptions, StartContainerOptions};
use bollard::exec::{CreateExecOptions, StartExecResults};
use bollard::Docker;
use bytes::{BufMut, BytesMut};
use futures_util::stream::StreamExt;
use futures_util::TryStreamExt;
use passwd::PasswdEntry;
use rand::Rng;
use std::collections::HashMap;
use std::io::Read;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum DockerContainerGuardError {
    #[error("Docker API error: {0}")]
    DockerError(#[from] bollard::errors::Error),

    #[error("File not found: {0}")]
    FileNotFound(String),

    #[error("Failed to extract file: {0}")]
    FileExtractionFailed(#[from] std::io::Error),

    #[error("Too many files in tarball")]
    TooManyFilesInTarball,

    #[error("Failed to parse password entry: {0}")]
    FailedToParsePasswdEntry(#[from] passwd::PasswdEntryError),

    #[error("User not found: {0}")]
    UserNotFound(String),
}

#[derive(Debug)]
pub struct DockerContainerGuard {
    pub id: String,
    pub image: String,
    docker: Docker,
}

impl DockerContainerGuard {
    // Spawns a new container using Bollard.
    //
    // The container is automatically cleaned up when the guard goes out of scope.
    pub async fn spawn(image_name: &str) -> Result<Self, DockerContainerGuardError> {
        let docker = Docker::connect_with_local_defaults()?;

        let container_name: String = rand::thread_rng()
            .sample_iter(&rand::distributions::Alphanumeric)
            .take(10)
            .map(char::from)
            .collect();

        docker
            .create_image(
                Some(bollard::image::CreateImageOptions {
                    from_image: image_name,
                    ..Default::default()
                }),
                None,
                None,
            )
            .try_collect::<Vec<_>>()
            .await?;

        let container = docker
            .create_container(
                Some(CreateContainerOptions {
                    name: container_name,
                    ..Default::default()
                }),
                Config {
                    image: Some(image_name),
                    cmd: Some(vec!["sh"]),
                    tty: Some(true),
                    ..Default::default()
                },
            )
            .await?;

        docker
            .start_container(&container.id, None::<StartContainerOptions<String>>)
            .await?;

        Ok(Self {
            id: container.id,
            image: image_name.to_string(),
            docker,
        })
    }

    /// Executes a command inside the container using Bollard.
    ///
    /// Returns the output as a String.
    pub async fn exec(&self, cmd: Vec<&str>) -> Result<String, bollard::errors::Error> {
        let exec_instance = self
            .docker
            .create_exec(
                &self.id,
                CreateExecOptions {
                    attach_stdout: Some(true),
                    attach_stderr: Some(true),
                    cmd: Some(cmd.iter().map(|s| s.to_string()).collect()),
                    ..Default::default()
                },
            )
            .await?;
        let start_exec_result = self.docker.start_exec(&exec_instance.id, None).await?;

        if let StartExecResults::Attached {
            output: out_stream, ..
        } = start_exec_result
        {
            let output = out_stream
                .filter_map(|chunk| async {
                    match chunk {
                        Ok(bollard::container::LogOutput::StdOut { message })
                        | Ok(bollard::container::LogOutput::StdErr { message }) => {
                            Some(String::from_utf8_lossy(&message).to_string())
                        }
                        _ => None,
                    }
                })
                .fold(String::new(), |mut acc, item| async move {
                    acc.push_str(&item);
                    acc
                })
                .await;

            return Ok(output);
        }

        Ok(String::new())
    }

    // Read a file from the container.
    pub async fn read_file(&self, path: &str) -> Result<String, DockerContainerGuardError> {
        let bytes = self
            .docker
            .download_from_container::<String>(
                &self.id,
                Some(bollard::container::DownloadFromContainerOptions { path: path.into() }),
            )
            .try_fold(BytesMut::new(), |mut bytes, b| async move {
                bytes.put(b);
                Ok(bytes)
            })
            .await?;

        if bytes.is_empty() {
            return Err(DockerContainerGuardError::FileNotFound(path.into()));
        }

        if let Some(file) = (tar::Archive::new(&bytes[..]).entries()?).next() {
            let mut s = String::new();
            file?.read_to_string(&mut s).unwrap();
            return Ok(s);
        }

        Err(DockerContainerGuardError::FileNotFound(path.into()))
    }

    // Get a HashMap of all users in the container.
    pub async fn get_users(
        &self,
    ) -> Result<HashMap<String, PasswdEntry>, DockerContainerGuardError> {
        let output = self.read_file("/etc/passwd").await?;

        output
            .lines()
            .map(|line| {
                PasswdEntry::from_line(line)
                    .map(|entry| (entry.name.clone(), entry))
                    .map_err(DockerContainerGuardError::from)
            })
            .collect()
    }

    // Get a specific user from the container.
    pub async fn get_user(&self, name: &str) -> Result<PasswdEntry, DockerContainerGuardError> {
        let users = self.get_users().await?;
        let user = users
            .get(name)
            .ok_or_else(|| DockerContainerGuardError::UserNotFound(name.into()))?;

        Ok(user.clone())
    }
}

impl Drop for DockerContainerGuard {
    fn drop(&mut self) {
        let docker = self.docker.clone();
        let container_id = self.id.clone();

        tokio::spawn(async move {
            docker
                .remove_container(
                    &container_id,
                    Some(bollard::container::RemoveContainerOptions {
                        force: true,
                        ..Default::default()
                    }),
                )
                .await
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_container_exec() -> Result<(), DockerContainerGuardError> {
        let guard =
            DockerContainerGuard::spawn("registry.atmosphere.dev/docker.io/library/alpine:latest")
                .await?;

        let output = guard.exec(vec!["echo", "hello from container"]).await?;
        assert!(output.contains("hello from container"));

        Ok(())
    }

    #[tokio::test]
    async fn test_container_read_file() -> Result<(), DockerContainerGuardError> {
        let guard =
            DockerContainerGuard::spawn("registry.atmosphere.dev/docker.io/library/alpine:latest")
                .await?;

        let file = guard.read_file("/usr/lib/os-release").await?;
        assert!(file.len() > 0);

        Ok(())
    }

    #[tokio::test]
    async fn test_container_get_user() -> Result<(), DockerContainerGuardError> {
        let guard =
            DockerContainerGuard::spawn("registry.atmosphere.dev/docker.io/library/alpine:latest")
                .await?;

        let user = guard.get_user("root").await?;
        assert_eq!(user.name, "root");

        Ok(())
    }
}
