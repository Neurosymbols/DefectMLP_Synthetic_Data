#!/usr/bin/env python3
"""
MongoDB insertion script for synthetic PCB data
"""

import pandas as pd
from pymongo import MongoClient, ASCENDING
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "mongo_uri": "mongodb://localhost:27017/",
    "database": "pcb_manufacturing",
    "collection": "synthetic_boards",
    "csv_file": "training_data_200k.csv",
    "batch_size": 10000
}

# ============================================================================
# PREPARE DOCUMENT
# ============================================================================

def prepare_document(row):
    """Convert DataFrame row to MongoDB document"""
    doc = {
        "board_id": f"PCB_{int(row['board_number'])}",
        "batch_id": int(row['batch_id']),
        "board_number": int(row['board_number']),
        
        "parameters": {
            "paste_volume_per_aperture": float(row['Paste volume per aperture']),
            "stencil_thickness": float(row['Stencil thickness']),
            "paste_viscosity": float(row['Paste viscosity']),
            "ambient_rh": float(row['Ambient RH']),
            "ambient_temperature": float(row['Ambient temperature'])
        },
        
        "labels": {
            "defect": row['Defect'],
            "mechanism_causes": row['mech causes'] if pd.notna(row['mech causes']) and row['mech causes'] != '' else None,
            "root_causes": row['root causes'] if pd.notna(row['root causes']) and row['root causes'] != '' else None
        },
        
        "temporal": {
            "hour_of_day": float(row['hour_of_day']),
            "stencil_batch": int(row['stencil_batch'])
        },
        
        "metadata": {
            "generated_at": datetime.utcnow(),
            "data_source": "synthetic_generator_v1",
            "schema_version": "1.0"
        }
    }
    
    return doc

# ============================================================================
# BULK INSERTION
# ============================================================================

def insert_data_bulk(df, collection, batch_size=10000):
    """Insert data in batches"""
    total_rows = len(df)
    documents = []
    
    print(f"Inserting {total_rows} documents...")
    
    for idx, row in df.iterrows():
        doc = prepare_document(row)
        documents.append(doc)
        
        if len(documents) >= batch_size:
            collection.insert_many(documents)
            print(f"Progress: {idx + 1}/{total_rows} ({(idx+1)/total_rows*100:.1f}%)")
            documents = []
    
    if documents:
        collection.insert_many(documents)
        print(f"✓ Inserted {total_rows} documents")

def store_in_mongo():
    # Connect
    print("Connecting to MongoDB...")
    client = MongoClient(CONFIG['mongo_uri'])
    db = client[CONFIG['database']]
    collection = db[CONFIG['collection']]
    
    # Load data
    print(f"\nLoading {CONFIG['csv_file']}...")
    df = pd.read_csv(CONFIG['csv_file'])
    print(f"Loaded {len(df)} rows")
    
    # Insert
    insert_data_bulk(df, collection, CONFIG['batch_size'])
    
    # Verify
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    total = collection.count_documents({})
    print(f"Total documents: {total:,}")

store_in_mongo()