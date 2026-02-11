extern crate ipnet;

mod routes;

use futures_util::stream::TryStreamExt;
use ipnet::IpNet;
use log::{error, info};
use netlink_packet_route::{
    AddressFamily,
    address::{AddressAttribute, AddressMessage},
    route::{RouteAttribute, RouteMessage, RouteScope},
};
use rtnetlink::{Handle, IpVersion};
use std::net::IpAddr;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum InterfaceError {
    #[error("Interface {0} not found")]
    NotFound(String),

    #[error(transparent)]
    NetlinkError(#[from] rtnetlink::Error),

    #[error(transparent)]
    IpNetError(#[from] ipnet::PrefixLenError),

    #[error(transparent)]
    RouteError(#[from] routes::RouteError),
}

#[derive(Error, Debug)]
pub enum InterfaceMigrationError {
    #[error(transparent)]
    InterfaceError(#[from] InterfaceError),

    #[error("IP configuration on both interfaces")]
    IpConflict,
}

pub struct Interface {
    name: String,
    index: u32,
    address_messages: Vec<AddressMessage>,
    route_messages: Vec<RouteMessage>,
}

impl Interface {
    pub async fn new(handle: &Handle, name: String) -> Result<Self, InterfaceError> {
        let index = handle
            .link()
            .get()
            .match_name(name.clone())
            .execute()
            .try_next()
            .await
            .map_err(|e| match e {
                rtnetlink::Error::NetlinkError(inner) if -inner.raw_code() == libc::ENODEV => {
                    InterfaceError::NotFound(name.clone())
                }
                _ => InterfaceError::NetlinkError(e),
            })?
            .map(|link| link.header.index)
            .ok_or_else(|| InterfaceError::NotFound(name.clone()))?;

        let address_messages: Vec<AddressMessage> = handle
            .address()
            .get()
            .set_link_index_filter(index)
            .execute()
            .map_err(InterfaceError::NetlinkError)
            .try_filter(|msg| futures::future::ready(msg.header.family == AddressFamily::Inet))
            .try_collect()
            .await?;

        let route_messages: Vec<RouteMessage> = handle
            .route()
            .get(IpVersion::V4)
            .execute()
            .map_err(InterfaceError::NetlinkError)
            .try_filter(move |route_msg| {
                let matches = route_msg
                    .attributes
                    .iter()
                    .any(|attr| matches!(attr, RouteAttribute::Oif(idx) if *idx == index))
                    && route_msg.header.kind != netlink_packet_route::route::RouteType::Local;

                futures_util::future::ready(matches)
            })
            .try_collect()
            .await?;

        Ok(Self {
            name,
            index,
            address_messages,
            route_messages,
        })
    }

    fn addresses(&self) -> Vec<IpNet> {
        self.address_messages
            .iter()
            .filter_map(|msg| {
                msg.attributes.iter().find_map(|nla| {
                    if let AddressAttribute::Address(ip) = nla {
                        IpNet::new(*ip, msg.header.prefix_len).ok()
                    } else {
                        None
                    }
                })
            })
            .collect()
    }

    fn routes(&self) -> Result<Vec<routes::Route>, routes::RouteError> {
        self.route_messages
            .iter()
            .filter_map(|msg| {
                if msg.header.scope == RouteScope::Link {
                    return None;
                }

                Some(routes::Route::from_message(msg.clone()))
            })
            .collect::<Result<Vec<routes::Route>, routes::RouteError>>()
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

    async fn restore(&self, handle: &Handle) -> Result<(), InterfaceError> {
        self.migrate_addresses_from_interface(handle, self).await?;
        self.migrate_routes_from_interface(handle, self).await?;

        Ok(())
    }

    async fn flush(&self, handle: &Handle) -> Result<(), InterfaceError> {
        for msg in self.address_messages.iter() {
            handle.address().del(msg.clone()).execute().await?;
        }

        // NOTE(mnaser): Once the interface has no more addresses, it will
        //               automatically lose all of it's routes.

        Ok(())
    }

    async fn migrate_addresses_from_interface(
        &self,
        handle: &Handle,
        src_interface: &Interface,
    ) -> Result<(), InterfaceError> {
        for msg in src_interface.address_messages.iter() {
            let ip = msg.attributes.iter().find_map(|nla| match nla {
                AddressAttribute::Address(ip) => Some(ip),
                _ => None,
            });

            if let Some(ip) = ip {
                handle
                    .address()
                    .add(self.index, *ip, msg.header.prefix_len)
                    .replace()
                    .execute()
                    .await?;
            }
        }

        Ok(())
    }

    async fn migrate_routes_from_interface(
        &self,
        handle: &Handle,
        src_interface: &Interface,
    ) -> Result<(), InterfaceError> {
        for route in src_interface.routes()?.iter() {
            let mut request = handle.route().add();
            request = request.protocol(route.protocol);

            match route.destination.addr() {
                IpAddr::V4(ipv4) => {
                    let mut request = request
                        .v4()
                        .replace()
                        .destination_prefix(ipv4, route.destination.prefix_len());

                    if let IpAddr::V4(gateway) = route.gateway {
                        request = request.gateway(gateway);
                    }

                    request.execute().await?;
                }
                IpAddr::V6(ipv6) => {
                    let mut request = request
                        .v6()
                        .replace()
                        .destination_prefix(ipv6, route.destination.prefix_len());

                    if let IpAddr::V6(gateway) = route.gateway {
                        request = request.gateway(gateway);
                    }

                    request.execute().await?;
                }
            }
        }

        Ok(())
    }

    pub async fn migrate_from_interface(
        &self,
        handle: &Handle,
        src_interface: &Interface,
    ) -> Result<(), InterfaceMigrationError> {
        self.up(handle).await?;

        match (
            src_interface.address_messages.is_empty(),
            self.address_messages.is_empty(),
        ) {
            (false, false) => {
                // Both source and destination interfaces have IPs assigned
                error!(
                    src_interface = src_interface.name.as_str(),
                    dst_interface = self.name.as_str(),
                    src_ip_addresses = format!("{:?}", src_interface.addresses()).as_str(),
                    dst_ip_addresses = format!("{:?}", self.addresses()).as_str();
                    "Both source and destination interfaces have IPs assigned. This is not safe in production, please fix manually."
                );

                Err(InterfaceMigrationError::IpConflict)
            }
            (false, true) => {
                // Source interface has IPs, destination interface has no IPs
                info!(
                    src_interface = src_interface.name.as_str(),
                    dst_interface = self.name.as_str(),
                    ip_addresses = format!("{:?}", src_interface.addresses()).as_str(),
                    routes = format!("{:?}", src_interface.routes()).as_str();
                    "Migrating IP addresses from interface to bridge."
                );

                if let Err(e) = src_interface.flush(handle).await {
                    error!(
                        src_interface = src_interface.name.as_str(),
                        error = e.to_string().as_str();
                        "Error while flushing IPs from source interface."
                    );

                    if let Err(restore_err) = src_interface.restore(handle).await {
                        error!(
                            src_interface = src_interface.name.as_str(),
                            error = restore_err.to_string().as_str();
                            "Error while restoring IPs to source interface."
                        );
                    }

                    return Err(InterfaceMigrationError::InterfaceError(e));
                }

                info!(
                    src_interface = src_interface.name.as_str(),
                    dst_interface = self.name.as_str();
                    "Successfully flushed IP addresses from source interface."
                );

                if let Err(e) = self
                    .migrate_addresses_from_interface(handle, src_interface)
                    .await
                {
                    error!(
                        dst_interface = self.name.as_str(),
                        error = e.to_string().as_str();
                        "Error while migrating IP addresses to destination interface."
                    );

                    if let Err(restore_err) = src_interface.restore(handle).await {
                        error!(
                            src_interface = src_interface.name.as_str(),
                            error = restore_err.to_string().as_str();
                            "Error while restoring IPs to source interface."
                        );
                    }

                    return Err(InterfaceMigrationError::InterfaceError(e));
                }

                info!(
                    src_interface = src_interface.name.as_str(),
                    dst_interface = self.name.as_str();
                    "Successfully migrated IP addresseses to new interface."
                );

                if let Err(e) = self
                    .migrate_routes_from_interface(handle, src_interface)
                    .await
                {
                    error!(
                        dst_interface = self.name.as_str(),
                        routes = format!("{:?}", src_interface.routes()).as_str(),
                        error = e.to_string().as_str();
                        "Error while migrating routes to destination interface."
                    );

                    if let Err(restore_err) = src_interface.restore(handle).await {
                        error!(
                            src_interface = src_interface.name.as_str(),
                            routes = format!("{:?}", src_interface.routes()).as_str(),
                            error = restore_err.to_string().as_str();
                            "Error while restoring source interface."
                        );
                    }

                    return Err(InterfaceMigrationError::InterfaceError(e));
                }

                Ok(())
            }
            (true, false) => {
                // Destination interface has IPs, source interface has no IPs
                info!(
                    src_interface = src_interface.name.as_str(),
                    dst_interface = self.name.as_str(),
                    ip_addresses = format!("{:?}", self.addresses()).as_str();
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
