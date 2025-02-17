use crate::RepositoryClient;
use async_trait::async_trait;
use octocrab::Octocrab;
use std::error::Error;
use std::sync::Arc;

pub struct Client {
    client: Arc<Octocrab>,
}

impl Client {
    pub fn new() -> Self {
      Client {
            client: octocrab::instance(),
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
        let commits = self
            .client
            .repos(repository.owner.clone(), repository.name.clone())
            .list_commits()
            .branch(branch)
            .send()
            .await?;

        Ok(commits.items[0].sha.clone())
    }
}
