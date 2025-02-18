pub mod github;
pub mod opendev;

use crate::clients::github::Client as GitHubClient;
use crate::clients::opendev::Client as OpenDevClient;

pub struct ClientSet {
    pub github: GitHubClient,
    pub opendev: OpenDevClient,
}

impl ClientSet {
    pub fn new() -> Self {
        ClientSet {
            github: GitHubClient::new(),
            opendev: OpenDevClient::new(),
        }
    }
}
