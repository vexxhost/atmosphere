use k8s_openapi::serde_json;
use kcr_monitoring_coreos_com::v1::prometheusrules::PrometheusRuleSpec;
use once_cell::sync::Lazy;
use rsjsonnet_front::Session;
use rsjsonnet_lang::arena::Arena;
use std::{collections::HashMap, path::Path};

static RULES: Lazy<HashMap<String, PrometheusRuleSpec>> = Lazy::new(|| {
    let path = Path::new("../../roles/kube_prometheus_stack/files/jsonnet/rules.jsonnet");

    let arena = Arena::new();
    let mut session = Session::new(&arena);

    let Some(thunk) = session.load_real_file(path) else {
        panic!("Failed to load jsonnet file");
    };

    let Some(value) = session.eval_value(&thunk) else {
        panic!("Failed to evaluate jsonnet file");
    };

    let Some(json_result) = session.manifest_json(&value, false) else {
        panic!("Failed to convert jsonnet to JSON");
    };

    serde_json::from_str(&json_result).unwrap()
});

pub fn load_rules() -> &'static HashMap<String, PrometheusRuleSpec> {
    &RULES
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;
    use tempfile::TempDir;

    #[test]
    fn test_promtool() {
        let mut tests: HashMap<String, serde_yaml::Value> = serde_yaml::from_reader(
            File::open("../../roles/kube_prometheus_stack/files/jsonnet/tests.yml").unwrap(),
        )
        .expect("failed to read tests.yml");

        let tempdir = TempDir::new().unwrap();
        let mut rule_files = Vec::new();

        for (name, rule) in load_rules() {
            let file_path = tempdir.path().join(format!("{}.yaml", name));

            serde_json::to_writer(File::create(&file_path).unwrap(), rule).unwrap();
            rule_files.push(file_path);
        }

        tests.insert(
            "rule_files".to_string(),
            serde_yaml::to_value(rule_files).unwrap(),
        );

        serde_json::to_writer(
            File::create(tempdir.path().join("tests.yaml")).unwrap(),
            &tests,
        )
        .expect("failed to write tests.yaml");

        // TODO(mnaser): JUnit output?
        let output = std::process::Command::new("promtool")
            .arg("test")
            .arg("rules")
            .arg(tempdir.path().join("tests.yaml"))
            .output()
            .expect("failed to execute promtool");

        if !output.status.success() {
            panic!(
                "promtool failed: {}",
                String::from_utf8_lossy(&output.stderr)
            );
        }
    }
}
