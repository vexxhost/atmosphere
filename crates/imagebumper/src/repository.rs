use crate::clients::ClientSet;
use crate::RepositoryClient;
use std::error::Error;
use url::Url;

pub struct Repository<'a> {
    pub owner: String,
    pub name: String,
    client: &'a dyn RepositoryClient,
}

impl<'a> Repository<'a> {
    pub fn from_url(clientset: &'a ClientSet, url: &str) -> Result<Self, Box<dyn Error>> {
        let url = url.trim_end_matches(".git");
        let parsed_url = Url::parse(url)?;
        let hostname = parsed_url.host_str().ok_or("Invalid repository URL")?;
        let parts: Vec<&str> = parsed_url
            .path_segments()
            .ok_or("Invalid repository URL")?
            .collect();
        if parts.len() < 2 {
            return Err("Invalid repository URL".into());
        }

        let client: &dyn RepositoryClient = match hostname {
            "opendev.org" => &clientset.opendev,
            "github.com" => &clientset.github,
            _ => return Err("Unsupported repository host".into()),
        };

        Ok(Repository {
            owner: parts[parts.len() - 2].to_string(),
            name: parts[parts.len() - 1].to_string(),
            client,
        })
    }

    pub async fn get_latest_commit(&self, branch: &str) -> Result<String, Box<dyn Error>> {
        self.client.get_latest_commit(self, branch).await
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_from_url_for_opendev() {
        let clientset = ClientSet::new();
        let repo =
            Repository::from_url(&clientset, "https://opendev.org/openstack/nova.git").unwrap();

        assert_eq!(repo.owner, "openstack");
        assert_eq!(repo.name, "nova");
    }

    #[tokio::test]
    async fn test_from_url_for_github() {
        let clientset = ClientSet::new();
        let repo =
            Repository::from_url(&clientset, "https://github.com/vexxhost/atmosphere.git").unwrap();

        assert_eq!(repo.owner, "vexxhost");
        assert_eq!(repo.name, "atmosphere");
    }
}
