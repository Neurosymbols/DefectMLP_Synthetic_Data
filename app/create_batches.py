# =====================================================================
# SCIENCE BEHIND NO OF BATCHES
# Target: 1,000 examples per class (ML minimum)

# Opens:
#   Current rate: 1.25%
#   Boards needed: 1,000 / 0.0125 = 80,000 boards
#   Batches: 80,000 / 5,000 = 16 batches

# Bridging (rarer, drives requirement):
#   Current rate: 1.09%
#   Boards needed: 1,000 / 0.0109 = 91,743 boards
#   Batches: 91,743 / 5,000 = 18.3 ≈ 19 batches minimum
  
# Safety margin (1.5x): 19 × 1.5 ≈ 29 batches
# Comfortable: 40-50 batches
# =====================================================================

import pandas as pd
from .main_sample import sample_with_drift_and_cycles_and_defects
# Generate 40 batches = 200,000 boards
all_batches = []

for batch_id in range(40):
    df_batch, oos = sample_with_drift_and_cycles_and_defects(
        n_samples=5000,  # Exact 5000 per batch
        random_seed=42 + batch_id,  # Different seed per batch
        start_hour=6 + (batch_id % 3) * 8  # Rotate shifts: 6AM, 2PM, 10PM
    )
    df_batch['batch_id'] = batch_id
    all_batches.append(df_batch)
    
    # Progress
    if (batch_id + 1) % 10 == 0:
        print(f"Generated {batch_id + 1} batches...")

# Combine
df_all = pd.concat(all_batches, ignore_index=True)

# # Verify
# print(f"\nTotal boards: {len(df_all)}")
# print(f"Expected defects:")
# print(f"  Opens: ~{int(200000 * 0.0125)} (target: 1000+)")
# print(f"  Bridging: ~{int(200000 * 0.0109)} (target: 1000+)")
# print("\nActual distribution:")
# print(df_all['Defect'].value_counts())

# Save
df_all.to_csv("training_data_200k_v4.csv", index=False)
'''

---

## Expected Results (40 batches = 200K boards)
```
No Defect:      195,300 (97.65%)
Open Circuit:    2,500 (1.25%) ✓ Exceeds 1,000 target
Solder Bridging: 2,200 (1.09%) ✓ Exceeds 1,000 target
```

---

## Why 40 Batches?

**Rule of Thumb**: 
- Need ~1,000 examples per class minimum
- Your rarer class (Bridging) is 1.09%
- 1,000 / 0.0109 / 5,000 = 18 batches minimum
- **Safety factor 2x** = 36 batches
- Round to **40 batches** (gives buffer for splits)

**Split strategy** (by batch, not random!):
```
Train: 28 batches (140K boards) → ~1,500 Bridging, ~1,750 Opens
Val:   6 batches (30K boards)   → ~330 Bridging, ~375 Opens  
Test:  6 batches (30K boards)   → ~330 Bridging, ~375 Opens
'''