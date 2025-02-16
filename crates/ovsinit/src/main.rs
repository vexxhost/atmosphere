use clap::Parser;
use env_logger::Env;
use log::error;
use rtnetlink::Handle;
use serde::Deserialize;
use std::{collections::HashMap, fs::File, path::PathBuf, process};
use tokio;

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Cli {
    #[arg(default_value = "/tmp/auto_bridge_add", help = "Path to the JSON file")]
    config: PathBuf,
}

#[derive(Deserialize)]
struct NetworkConfig {
    #[serde(flatten)]
    bridges: HashMap<String, String>,
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    let env = Env::default()
        .filter_or("MY_LOG_LEVEL", "info")
        .write_style_or("MY_LOG_STYLE", "always");
    env_logger::init_from_env(env);

    let file = match File::open(&cli.config) {
        Ok(file) => file,
        Err(e) => {
            error!("Failed to open file: {}", e);

            process::exit(1);
        }
    };

    let network_config: NetworkConfig = match
        serde_json::from_reader(file) {
        Ok(network_config) => network_config,
        Err(e) => {
            error!("Failed to parse JSON: {}", e);

            process::exit(1);
        }
    };

    let (connection, handle, _) = rtnetlink::new_connection().expect("Failed to create connection");
    tokio::spawn(connection);

    for (bridge_name, interface_name) in network_config.bridges {
        let interface = get_interface(&handle, &interface_name).await;
        let bridge = get_interface(&handle, &bridge_name).await;

        if let Err(e) = bridge.migrate_from_interface(&handle, &interface).await {
            error!(
                "Failed to migrate from {} to {}: {}",
                interface_name, bridge_name, e
            );

            process::exit(1);
        }
    }
}

async fn get_interface(handle: &Handle, name: &str) -> ovsinit::Interface {
    match ovsinit::Interface::new(handle, name.to_string()).await {
        Ok(interface) => interface,
        Err(ovsinit::InterfaceError::NotFound(name)) => {
            error!(interface = name.as_str(); "Interface not found.");
            process::exit(1);
        }
        Err(e) => {
            error!(error = e.to_string().as_str(); "Failed to lookup interface.");
            process::exit(1);
        }
    }
}
