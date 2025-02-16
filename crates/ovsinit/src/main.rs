extern crate ipnet;

use env_logger::Env;
use futures_util::pin_mut;
use futures_util::stream::TryStreamExt;
use ipnet::IpNet;
use log::{debug, error, info, trace, warn};
use netlink_packet_route::route::RouteAttribute;
use netlink_packet_route::{address::AddressAttribute, AddressFamily};
use rtnetlink::{Handle, IpVersion};
use std::process;
use thiserror::Error;
use tokio;

#[tokio::main]
async fn main() {
    let env = Env::default()
        .filter_or("MY_LOG_LEVEL", "info")
        .write_style_or("MY_LOG_STYLE", "always");
    env_logger::init_from_env(env);

    let (connection, handle, _) = rtnetlink::new_connection().expect("Failed to create connection");
    tokio::spawn(connection);

    migrate_ip_from_nic(&handle, String::from("eth0"), String::from("br-ex")).await;
    // let (connection, handle, _) = new_connection().expect("Failed to create connection");
    // tokio::spawn(connection);

    // let iface_name = "eth0";
    // let iface_index = handle
    //     .link()
    //     .get()
    //     .match_name(iface_name.to_string())
    //     .execute()
    //     .try_next()
    //     .await
    //     .map_err(|e| match e {
    //         rtnetlink::Error::NetlinkError(inner) if inner.raw_code() == -libc::ENODEV => {
    //             eprintln!("Error: Interface '{}' not found", iface_name);
    //             process::exit(1);
    //         }
    //         _ => {
    //             eprintln!("Failed to lookup interface: {}", e);
    //             process::exit(1);
    //         }
    //     })
    //     .unwrap()
    //     .map(|link| link.header.index)
    //     .unwrap();

    // let v4_routes = handle
    //     .route()
    //     .get(IpVersion::V4)
    //     .execute()
    //     .map_err(|e| match e {
    //         _ => {
    //             eprintln!("Failed to lookup IPv4 routes: {}", e);
    //             process::exit(1);
    //         }
    //     })
    //     .try_filter(move |route_msg| {
    //         let matches = route_msg
    //             .attributes
    //             .iter()
    //             .any(|attr| matches!(attr, RouteAttribute::Oif(idx) if *idx == iface_index));

    //         futures_util::future::ready(matches)
    //     });

    // let v6_routes = handle
    //     .route()
    //     .get(IpVersion::V6)
    //     .execute()
    //     .map_err(|e| match e {
    //         _ => {
    //             eprintln!("Failed to lookup IPv6 routes: {}", e);
    //             process::exit(1);
    //         }
    //     })
    //     .try_filter(move |route_msg| {
    //         let matches = route_msg
    //             .attributes
    //             .iter()
    //             .any(|attr| matches!(attr, RouteAttribute::Oif(idx) if *idx == iface_index));

    //         futures_util::future::ready(matches)
    //     });

    // let routes_stream = futures_util::stream::select(v4_routes, v6_routes);

    // // Pin the stream so we can safely call try_next.
    // pin_mut!(routes_stream);

    // // Process the stream.
    // while let Some(route) = routes_stream.try_next().await.unwrap() {
    //     println!("{:?}", route);
    // }

    // let ip_stream = handle
    //     .address()
    //     .get()
    //     .set_link_index_filter(iface_index)
    //     .execute();

    // pin_mut!(ip_stream);

    // while let Some(ip) = ip_stream.try_next().await.unwrap() {
    //     println!("{:?}", ip);
    // }

    // TODO: safely store all the ips
    // TODO: safely store all the routes
    // TODO: flush ip for the src interface
    // TDOO: add routes/ip for the dst interface
    // NICE TO HAVE: single transaction to flush/add ips
    // TODO: rollback if anything fails
    // TODO: safety assertions
}

#[derive(Error, Debug)]
enum InterfaceError {
    #[error("Interface {0} not found")]
    NotFound(String),

    #[error(transparent)]
    NetlinkError(#[from] rtnetlink::Error),

    #[error(transparent)]
    IpNetError(#[from] ipnet::PrefixLenError),

    #[error("IP configuration on both interfaces")]
    IpConflict,
}

struct Interface {
    name: String,
    index: u32,
    addresses: Vec<IpNet>,
}

impl Interface {
    async fn new(handle: &Handle, name: String) -> Result<Self, InterfaceError> {
        let index = handle
            .link()
            .get()
            .match_name(name.clone())
            .execute()
            .try_next()
            .await
            .map_err(InterfaceError::NetlinkError)?
            .map(|link| link.header.index)
            .ok_or_else(|| InterfaceError::NotFound(name.clone()))?;

        let addresses = handle
            .address()
            .get()
            .set_link_index_filter(index)
            .execute()
            .map_err(InterfaceError::NetlinkError)
            .try_filter(|msg| futures::future::ready(msg.header.family == AddressFamily::Inet))
            .try_fold(Vec::new(), |mut addresses, msg| async move {
                for nla in msg.attributes.into_iter() {
                    if let AddressAttribute::Address(ip) = nla {
                        let ip = IpNet::new(ip, msg.header.prefix_len)
                            .map_err(InterfaceError::IpNetError)?;

                        addresses.push(ip);
                    }
                }

                Ok(addresses)
            })
            .await?;

        Ok(Self {
            name,
            index,
            addresses,
        })
    }

    async fn up(&self, handle: &Handle) -> Result<(), InterfaceError> {
        handle
            .link()
            .set(self.index)
            .up()
            .execute()
            .await
            .map_err(InterfaceError::NetlinkError)
    }

    async fn migrate_ip_from_interface(&self, handle: &Handle, src_interface: &Interface) -> Result<(), InterfaceError> {
        self.up(handle).await?;

        match (
            src_interface.addresses.is_empty(),
            self.addresses.is_empty(),
        ) {
            (false, false) => {
                // Both source and destination interfaces have IPs assigned
                error!(
                    src_interface = src_interface.name.as_str(),
                    dst_interface = self.name.as_str(),
                    src_ip_addresses = format!("{:?}", src_interface.addresses).as_str(),
                    dst_ip_addresses = format!("{:?}", self.addresses).as_str();
                    "Both source and destination interfaces have IPs assigned. This is not safe in production, please fix manually."
                );

                Err(InterfaceError::IpConflict)
            }
            (false, true) => {
                // Source interface has IPs, destination interface has no IPs
                info!(
                    src_interface = src_interface.name.as_str(),
                    dst_interface = self.name.as_str(),
                    ip_addresses = format!("{:?}", src_interface.addresses).as_str();
                    "Migrating IP addresses from interface to bridge."
                );

                // ip addr flush dev ${src_nic}
                // if [ $? -ne 0 ] ; then
                //   ip addr add ${ip}/${prefix} dev ${src_nic}
                //   echo "Error while flushing IP from ${src_nic}."
                //   exit 1
                // fi

                // ip addr add ${ip}/${prefix} dev "${bridge_name}"
                // if [ $? -ne 0 ] ; then
                //   echo "Error assigning IP to bridge "${bridge_name}"."
                //   ip addr add ${ip}/${prefix} dev ${src_nic}
                //   exit 1
                // fi

                Ok(())
            }
            (true, false) => {
                // Destination interface has IPs, source interface has no IPs
                info!(
                    src_interface = src_interface.name.as_str(),
                    dst_interface = self.name.as_str(),
                    ip_addresses = format!("{:?}", self.addresses).as_str();
                    "Bridge already has IPs assigned. Skipping migration."
                );

                Ok(())
            }
            (true, true) => {
                // Neither interface has IPs
                info!(
                    src_interface = src_interface.name.as_str(),
                    dst_interface = self.name.as_str();
                    "Neither interface nor bridge have IPs assigned. Skipping migration."
                );

                Ok(())
            }
        }
    }
}

async fn migrate_ip_from_nic(handle: &Handle, interface: String, bridge: String) {
    // TODO: get rid of all unwraps and switch to thiserror

    let src_interface = Interface::new(&handle, interface).await.unwrap();
    let dst_interface = Interface::new(&handle, bridge).await.unwrap();

    dst_interface.migrate_ip_from_interface(handle, &src_interface).await.unwrap();
}
