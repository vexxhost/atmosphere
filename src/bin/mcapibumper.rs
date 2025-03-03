use git2::Repository;
use indoc::indoc;
use regex::Regex;
use serde::Deserialize;
use std::path::Path;
use tokio::fs;

#[derive(Deserialize)]
struct PyPiPackageResponse {
    info: PyPiPackageInfo,
}

#[derive(Deserialize)]
struct PyPiPackageInfo {
    version: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let version = reqwest::get("https://pypi.org/pypi/magnum-cluster-api/json")
        .await?
        .json::<PyPiPackageResponse>()
        .await?
        .info
        .version;

    // Dockerfile
    let path = "images/magnum/Dockerfile";
    let content = fs::read_to_string(path).await?;
    let re = Regex::new(r"(magnum-cluster-api==)(\S+)")?;
    let updated = re.replace(&content, format!("${{1}}{}", version));
    fs::write(path, updated.into_owned()).await?;

    // Release notes
    let version_hash = format!("{:x}", md5::compute(&version));
    let release_note_path = format!("releasenotes/notes/bump-mcapi-{}.yaml", &version_hash[..16]);
    let release_note = format!(
        indoc!(
            r#"
            fixes:
              - The Cluster API driver for Magnum has been bumped to {} to improve
                stability, fix bugs and add new features.
            "#
        ),
        version
    );
    fs::write(&release_note_path, &release_note).await?;

    // Git commit
    let repo = Repository::discover(".")?;
    let mut index = repo.index()?;
    index.add_path(Path::new(path))?;
    index.add_path(Path::new(&release_note_path))?;
    index.write()?;
    let tree_id = index.write_tree()?;
    let tree = repo.find_tree(tree_id)?;
    let parent = repo.head()?.peel_to_commit()?;
    let sig = repo.signature()?;
    let mut commit_message = format!("Bump Magnum Cluster API to {}", version);
    git2_hooks::hooks_commit_msg(&repo, None, &mut commit_message)?;
    repo.commit(
        Some("HEAD"),
        &sig,
        &sig,
        commit_message.as_str(),
        &tree,
        &[&parent],
    )?;

    Ok(())
}
