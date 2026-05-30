// @generated — emitted by agentarmy-forge.
//
//   forge.version: 0.1.0
//   model.version: 1.0.0
//   source.uri:    file:///work/reference.model.yaml
//
//   DO NOT EDIT. Re-run forge against the source ontology to regenerate.
#![allow(dead_code)]

use serde::{Deserialize, Serialize};

/// Knowledge document
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Document {
    pub id: String,
    pub title: String,
    pub body: Option<String>,
    pub word_count: i32,
    pub created_at: String,
    pub author: Option<Box<User>>,
}

/// Platform user
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct User {
    pub id: String,
    pub handle: String,
    pub created_at: String,
    #[serde(default)]
    pub documents: Vec<Document>,
}
