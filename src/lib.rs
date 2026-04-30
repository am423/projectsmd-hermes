//! projectsmd library.
//!
//! Public API for parsing, validating, and rendering project.md files.

pub mod commands;
pub mod decisions;
pub mod frontmatter;
pub mod project;
pub mod render;
pub mod requirements;
pub mod sections;
pub mod session_log;
pub mod skill;
pub mod state;
pub mod tasks;
pub mod template;
pub mod validate;

pub use project::Project;
