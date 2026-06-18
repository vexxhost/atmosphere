use log::info;
use serde::Deserialize;
use std::collections::HashMap;
use std::{fs::File, path::PathBuf};
use thiserror::Error;

#[derive(Deserialize)]
pub struct NetworkConfig {
    #[serde(flatten)]
    pub bridges: HashMap<String, Option<String>>,
}

#[derive(Debug, Error)]
pub enum NetworkConfigError {
    #[error("Failed to open file: {0}")]
    OpenFile(#[from] std::io::Error),

    #[error("Failed to parse JSON: {0}")]
    ParseJson(#[from] serde_json::Error),
}

impl NetworkConfig {
    pub fn from_path(path: &PathBuf) -> Result<Self, NetworkConfigError> {
        let file = File::open(path)?;
        NetworkConfig::from_file(file)
    }

    pub fn from_file(file: File) -> Result<Self, NetworkConfigError> {
        let config: NetworkConfig = serde_json::from_reader(file)?;
        Ok(config)
    }

    pub fn bridges_with_interfaces_iter(&self) -> impl Iterator<Item = (&String, &String)> {
        self.bridges.iter().filter_map(|(k, v)| {
            if let Some(v) = v {
                Some((k, v))
            } else {
                info!(bridge = k.as_str(); "Bridge has no interface, skipping.");

                None
            }
        })
    }

    #[allow(dead_code)]
    pub fn from_string(json: &str) -> Result<Self, NetworkConfigError> {
        let config: NetworkConfig = serde_json::from_str(json)?;
        Ok(config)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_null_interface() {
        let config = NetworkConfig::from_string("{\"br-ex\": null}").unwrap();

        assert_eq!(config.bridges.len(), 1);
        assert_eq!(config.bridges.get("br-ex"), Some(&None));
    }

    #[test]
    fn test_bridges_with_interfaces_iter_with_null_interface() {
        let config = NetworkConfig::from_string("{\"br-ex\": null}").unwrap();

        let mut iter = config.bridges_with_interfaces_iter();
        assert_eq!(iter.next(), None);
    }

    #[test]
    fn test_bridges_with_interfaces_iter_with_interface() {
        let config = NetworkConfig::from_string("{\"br-ex\": \"bond0\"}").unwrap();

        let mut iter = config.bridges_with_interfaces_iter();
        assert_eq!(
            iter.next(),
            Some((&"br-ex".to_string(), &"bond0".to_string()))
        );
    }
}
