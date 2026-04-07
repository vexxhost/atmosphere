mod config;

use clap::Parser;
use env_logger::Env;
use log::error;
use rtnetlink::Handle;
use std::{path::PathBuf, process};

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Cli {
    #[arg(default_value = "/tmp/auto_bridge_add", help = "Path to the JSON file")]
    config: PathBuf,
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();

    let env = Env::default()
        .filter_or("MY_LOG_LEVEL", "info")
        .write_style_or("MY_LOG_STYLE", "always");
    env_logger::init_from_env(env);

    let network_config = match config::NetworkConfig::from_path(&cli.config) {
        Ok(network_config) => network_config,
        Err(e) => {
            error!("Failed to load network config: {}", e);

            process::exit(1);
        }
    };

    let (connection, handle, _) = rtnetlink::new_connection().expect("Failed to create connection");
    tokio::spawn(connection);

    for (bridge_name, interface_name) in network_config.bridges_with_interfaces_iter() {
        let interface = get_interface(&handle, interface_name).await;
        let bridge = get_interface(&handle, bridge_name).await;

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
