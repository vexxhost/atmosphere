use crate::RepositoryClient;
use async_trait::async_trait;
use gitea_sdk::Auth;
use gitea_sdk::Client as GiteaClient;
use std::error::Error;

pub struct Client {
    client: GiteaClient,
}

impl Client {
    pub fn new() -> Self {
        Client {
            client: GiteaClient::new("https://opendev.org", Auth::None::<String>),
        }
    }
}

#[async_trait]
impl RepositoryClient for Client {
    async fn get_latest_commit(
        &self,
        repository: &crate::repository::Repository,
        branch: &str,
    ) -> Result<String, Box<dyn Error>> {
        let branch_info = self
            .client
            .repos(repository.owner.clone(), repository.name.clone())
            .get_branch(branch)
            .send(&self.client)
            .await?;

        Ok(branch_info.commit.id)
    }
}
