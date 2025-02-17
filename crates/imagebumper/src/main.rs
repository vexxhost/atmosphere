use clap::Parser;
use imagebumper::clients::ClientSet;
use imagebumper::repository::Repository;
use log::error;
use log::{info, warn};
use regex::Regex;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use tokio::fs;
use tokio::io::AsyncWriteExt;

#[derive(Parser, Debug)]
#[clap(author, version, about)]
struct Args {
    #[clap(short, long)]
    branch: String,

    #[clap(required = true)]
    files: Vec<PathBuf>,
}

fn get_repo_map(clientset: &ClientSet) -> HashMap<&'static str, Repository> {
    let mut map = HashMap::new();

    map.insert(
        "BARBICAN_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/barbican.git").unwrap(),
    );
    map.insert(
        "CINDER_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/cinder.git").unwrap(),
    );
    map.insert(
        "DESIGNATE_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/designate.git").unwrap(),
    );
    map.insert(
        "GLANCE_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/glance.git").unwrap(),
    );
    map.insert(
        "HEAT_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/heat.git").unwrap(),
    );
    map.insert(
        "HORIZON_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/horizon.git").unwrap(),
    );
    map.insert(
        "IRONIC_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/ironic.git").unwrap(),
    );
    map.insert(
        "KEYSTONE_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/keystone.git").unwrap(),
    );
    map.insert(
        "KUBERNETES_ENTRYPOINT_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/airship/kubernetes-entrypoint").unwrap(),
    );
    map.insert(
        "MAGNUM_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/magnum.git").unwrap(),
    );
    map.insert(
        "MANILA_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/manila.git").unwrap(),
    );
    map.insert(
        "NETOFFLOAD_GIT_REF",
        Repository::from_url(clientset, "https://github.com/vexxhost/netoffload.git").unwrap(),
    );
    map.insert(
        "NEUTRON_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/neutron.git").unwrap(),
    );
    map.insert(
        "NEUTRON_VPNAAS_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/neutron-vpnaas.git").unwrap(),
    );
    map.insert(
        "NETWORKING_BAREMETAL_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/networking-baremetal.git").unwrap(),
    );
    map.insert(
        "POLICY_SERVER_GIT_REF",
        Repository::from_url(clientset, "https://github.com/vexxhost/neutron-policy-server.git").unwrap(),
    );
    map.insert(
        "LOG_PASER_GIT_REF",
        Repository::from_url(clientset, "https://github.com/vexxhost/neutron-ovn-network-logging-parser.git")
            .unwrap(),
    );
    map.insert(
        "NOVA_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/nova.git").unwrap(),
    );
    map.insert(
        "SCHEDULER_FILTERS_GIT_REF",
        Repository::from_url(clientset, "https://github.com/vexxhost/nova-scheduler-filters.git").unwrap(),
    );
    map.insert(
        "OCTAVIA_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/octavia.git").unwrap(),
    );
    map.insert(
        "REQUIREMENTS_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/requirements.git").unwrap(),
    );
    map.insert(
        "PLACEMENT_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/placement.git").unwrap(),
    );
    map.insert(
        "STAFFELN_GIT_REF",
        Repository::from_url(clientset, "https://github.com/vexxhost/staffeln.git").unwrap(),
    );
    map.insert(
        "TEMPEST_GIT_REF",
        Repository::from_url(clientset, "https://opendev.org/openstack/tempest.git").unwrap(),
    );

    map
}

async fn update_dockerfile(clientset: &ClientSet, path: &Path, branch: &str) -> Result<(), Box<dyn std::error::Error>> {
    let content = fs::read_to_string(path).await?;
    let re = Regex::new(r"(ARG\s+(\w+_GIT_REF)=)(\S+)")?;
    let mut new_content = content.clone();

    for cap in re.captures_iter(&content) {
        let arg_name = cap.get(2).unwrap().as_str();
        if let Some(repo) = get_repo_map(clientset).get(arg_name) {
            let new_git_ref = match repo.get_latest_commit(branch).await {
                Ok(commit) => commit,
                Err(e) => {
                    error!(arg = arg_name, error = e.to_string().as_str().trim(); "Failed to get latest commit");
                    continue;
                }
            };

            new_content = new_content.replace(
                &format!("{}{}", &cap[1], &cap[3]),
                &format!("{}{}", &cap[1], new_git_ref),
            );

            info!(arg = arg_name, path = path.to_str(), ref = new_git_ref.as_str(); "Updated Dockerfile");
        } else {
            error!(arg = arg_name; "No repository URL found.");
        }
    }

    if new_content != content {
        let mut file = fs::File::create(path).await?;
        file.write_all(new_content.as_bytes()).await?;
    }
    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    let args = Args::parse();

    let clientset = ClientSet::new();

    for file_path in args.files {
        if file_path.is_file() {
            update_dockerfile(&clientset, &file_path, &args.branch).await?;
        } else {
            warn!("{:?} is not a file, skipping", file_path);
        }
    }

    Ok(())
}
