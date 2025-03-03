default:
  just --list

bump-magnum-cluster-api:
  cargo run --bin mcapibumper
