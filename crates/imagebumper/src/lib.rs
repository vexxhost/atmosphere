pub mod repository;
pub mod clients;

use async_trait::async_trait;
use std::any::Any;
use std::error::Error;

#[async_trait]
pub trait RepositoryClient: Any + Send + Sync {
    async fn get_latest_commit(
        &self,
        repository: &crate::repository::Repository,
        branch: &str,
    ) -> Result<String, Box<dyn Error>>;
}
