use rustainers::DockerContainerGuard;
use rustainers::DockerContainerGuardError;
use std::env;

#[tokio::test]
async fn test_nova_ssh() -> Result<(), DockerContainerGuardError> {
    let guard = DockerContainerGuard::spawn(&format!(
        "{}/nova-ssh:{}",
        env::var("REGISTRY").unwrap_or_else(|_| "harbor.atmosphere.dev/library".to_string()),
        env::var("TAG").unwrap_or_else(|_| "main".to_string())
    ))
    .await?;

    let user = guard.get_user("nova").await?;
    assert_eq!(user.uid, 42424);
    assert_eq!(user.gid, 42424);
    assert_eq!(user.dir, "/var/lib/nova");
    assert_eq!(user.shell, "/bin/bash");

    Ok(())
}
