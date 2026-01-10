import matplotlib.pyplot as plt
import json

with open("./folder_1/out_of_spec.json") as f:
    data = json.load(f)

for d in data:
    d.pop("seed")
    d.pop("count")
    # Extract plotting lists
    specs = list(d.keys())
    below_lsl = [d[s]["below_lsl"] for s in specs]
    above_usl = [d[s]["above_usl"] for s in specs]

    x = range(len(specs))

    plt.figure(figsize=(12, 6))

    # Plot bars
    plt.bar(x, below_lsl, label="Below LSL")
    plt.bar(x, above_usl, bottom=below_lsl, label="Above USL")

    # Labels & formatting
    plt.xticks(x, specs, rotation=45, ha="right")
    plt.ylabel("Out-of-spec count")
    plt.title("Out-of-spec numbers per specification")
    plt.legend()

    plt.tight_layout()
    plt.savefig("attr_oos_freq.png", dpi=300, bbox_inches='tight')
    plt.close()
    break
