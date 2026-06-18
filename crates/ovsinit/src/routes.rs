use ipnet::IpNet;
use netlink_packet_route::{
    AddressFamily,
    route::{RouteAddress, RouteAttribute, RouteMessage, RouteProtocol},
};
use std::{
    fmt,
    net::{IpAddr, Ipv4Addr, Ipv6Addr},
};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum RouteError {
    #[error("Invalid gateway")]
    InvalidGateway,

    #[error("Invalid destination")]
    InvalidDestination,

    #[error("Invalid prefix length")]
    InvalidPrefixLength,

    #[error("Missing gateway")]
    MissingGateway,

    #[error("Missing destination")]
    MissingDestination,
}

pub struct Route {
    pub protocol: RouteProtocol,
    pub destination: IpNet,
    pub gateway: IpAddr,
}

impl fmt::Debug for Route {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{} via {}", self.destination, self.gateway)
    }
}

impl Route {
    pub fn from_message(message: RouteMessage) -> Result<Self, RouteError> {
        let mut gateway = None;
        let mut destination = None;

        for nla in message.attributes.iter() {
            if let RouteAttribute::Gateway(ip) = nla {
                gateway = match ip {
                    RouteAddress::Inet(ip) => Some(IpAddr::V4(*ip)),
                    RouteAddress::Inet6(ip) => Some(IpAddr::V6(*ip)),
                    _ => return Err(RouteError::InvalidGateway),
                };
            }

            if let RouteAttribute::Destination(ref ip) = nla {
                destination = match ip {
                    RouteAddress::Inet(ip) => Some(
                        IpNet::new(IpAddr::V4(*ip), message.header.destination_prefix_length)
                            .map_err(|_| RouteError::InvalidPrefixLength)?,
                    ),
                    RouteAddress::Inet6(ip) => Some(
                        IpNet::new(IpAddr::V6(*ip), message.header.destination_prefix_length)
                            .map_err(|_| RouteError::InvalidPrefixLength)?,
                    ),
                    _ => return Err(RouteError::InvalidDestination),
                };
            }
        }

        let gateway = match gateway {
            Some(gateway) => gateway,
            None => return Err(RouteError::MissingGateway),
        };

        let destination = match destination {
            Some(destination) => destination,
            None => match message.header.address_family {
                AddressFamily::Inet => IpNet::new(IpAddr::V4(Ipv4Addr::UNSPECIFIED), 0)
                    .map_err(|_| RouteError::InvalidPrefixLength)?,
                AddressFamily::Inet6 => IpNet::new(IpAddr::V6(Ipv6Addr::UNSPECIFIED), 0)
                    .map_err(|_| RouteError::InvalidPrefixLength)?,
                _ => return Err(RouteError::InvalidDestination),
            },
        };

        Ok(Route {
            protocol: message.header.protocol,
            destination,
            gateway,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use netlink_packet_route::AddressFamily;
    use std::net::Ipv4Addr;

    #[tokio::test]
    async fn test_default_ipv4_route() {
        let mut message = RouteMessage::default();

        message.header.address_family = AddressFamily::Inet;
        message.header.destination_prefix_length = 0;
        message.header.protocol = RouteProtocol::Static;
        message
            .attributes
            .push(RouteAttribute::Gateway(RouteAddress::Inet(Ipv4Addr::new(
                192, 168, 1, 1,
            ))));

        let route = Route::from_message(message).unwrap();

        assert_eq!(route.protocol, RouteProtocol::Static);
        assert_eq!(
            route.destination,
            IpNet::new(IpAddr::V4(Ipv4Addr::UNSPECIFIED), 0).unwrap()
        );
        assert_eq!(route.gateway, IpAddr::V4(Ipv4Addr::new(192, 168, 1, 1)));
    }

    #[tokio::test]
    async fn test_default_ipv6_route() {
        let mut message = RouteMessage::default();

        message.header.address_family = AddressFamily::Inet6;
        message.header.destination_prefix_length = 0;
        message.header.protocol = RouteProtocol::Static;
        message
            .attributes
            .push(RouteAttribute::Gateway(RouteAddress::Inet6(Ipv6Addr::new(
                0, 0, 0, 0, 0, 0, 0, 1,
            ))));

        let route = Route::from_message(message).unwrap();

        assert_eq!(route.protocol, RouteProtocol::Static);
        assert_eq!(
            route.destination,
            IpNet::new(IpAddr::V6(Ipv6Addr::UNSPECIFIED), 0).unwrap()
        );
        assert_eq!(
            route.gateway,
            IpAddr::V6(Ipv6Addr::new(0, 0, 0, 0, 0, 0, 0, 1))
        );
    }
}
