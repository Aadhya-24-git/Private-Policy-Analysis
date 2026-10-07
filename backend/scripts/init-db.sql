-- ==============================================================================
-- AI-Powered Fine Print Auditor - Database Initialization Script
-- Automatically executed upon container first run by PostgreSQL entrypoint
-- ==============================================================================

-- Enable pgvector extension for high-dimensional semantic clause embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension for unique document, clause, finding, and chat identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
