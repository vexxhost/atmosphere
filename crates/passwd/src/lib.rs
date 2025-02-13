use std::num::ParseIntError;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum PasswdEntryError {
    #[error("Failed to parse ID: {0}")]
    FailedToParseID(#[from] ParseIntError),

    #[error("Invalid passwd entry: {0}")]
    InvalidPasswdEntry(String),
}

#[derive(Debug, Clone)]
pub struct PasswdEntry {
    pub name: String,
    pub passwd: String,
    pub uid: u32,
    pub gid: u32,
    pub gecos: String,
    pub dir: String,
    pub shell: String,
}

impl PasswdEntry {
    pub fn from_line(line: &str) -> Result<PasswdEntry, PasswdEntryError> {
        let parts: Vec<&str> = line.split(":").map(|part| part.trim()).collect();

        if parts.len() != 7 {
            return Err(PasswdEntryError::InvalidPasswdEntry(line.to_string()));
        }

        Ok(PasswdEntry {
            name: parts[0].to_string(),
            passwd: parts[1].to_string(),
            uid: parts[2].parse()?,
            gid: parts[3].parse()?,
            gecos: parts[4].to_string(),
            dir: parts[5].to_string(),
            shell: parts[6].to_string(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_from_line_valid() {
        let line = "username:x:1000:1000:User Name:/home/username:/bin/bash";
        let entry = PasswdEntry::from_line(line).unwrap();
        assert_eq!(entry.name, "username");
        assert_eq!(entry.passwd, "x");
        assert_eq!(entry.uid, 1000);
        assert_eq!(entry.gid, 1000);
        assert_eq!(entry.gecos, "User Name");
        assert_eq!(entry.dir, "/home/username");
        assert_eq!(entry.shell, "/bin/bash");
    }

    #[test]
    fn test_from_line_invalid_uid() {
        let line = "username:x:invalid:1000:User Name:/home/username:/bin/bash";
        let result = PasswdEntry::from_line(line);
        assert!(result.is_err());
    }

    #[test]
    fn test_from_line_invalid_gid() {
        let line = "username:x:1000:invalid:User Name:/home/username:/bin/bash";
        let result = PasswdEntry::from_line(line);
        assert!(result.is_err());
    }

    #[test]
    fn test_from_line_missing_fields() {
        let line = "username:x:1000:1000:User Name:/home/username";
        let result = PasswdEntry::from_line(line);
        assert!(result.is_err());
    }
}
