-- SurplusLink Engine Database Schema
-- Run this in your Supabase SQL Editor to set up the tables and indices.

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Listings Table
CREATE TABLE IF NOT EXISTS listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity NUMERIC DEFAULT 1,
    unit TEXT DEFAULT 'units',
    description TEXT,
    location_lat DOUBLE PRECISION NOT NULL,
    location_lng DOUBLE PRECISION NOT NULL,
    location_name TEXT,
    status TEXT NOT NULL DEFAULT 'Available', -- 'Available', 'Processing', 'Matched', 'Completed', 'Archived'
    seller_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index on status for high-performance polling/filtering
CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status);
CREATE INDEX IF NOT EXISTS idx_listings_created_at ON listings(created_at DESC);

-- 2. Scraped Leads Table
CREATE TABLE IF NOT EXISTS scraped_leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    business_name TEXT NOT NULL,
    address TEXT,
    phone_number TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    distance_km DOUBLE PRECISION,
    query_used TEXT,
    lead_status TEXT NOT NULL DEFAULT 'Discovered', -- 'Discovered', 'Contacted', 'Qualified', 'Converted', 'Rejected'
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index on listing_id and lead_status
CREATE INDEX IF NOT EXISTS idx_scraped_leads_listing_id ON scraped_leads(listing_id);
CREATE INDEX IF NOT EXISTS idx_scraped_leads_status ON scraped_leads(lead_status);

-- Optional: Enable Supabase Realtime publication on listings table
ALTER PUBLICATION supabase_realtime ADD TABLE listings;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS description text;