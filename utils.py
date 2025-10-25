import numpy as np

def export_policy(policy_table, filename_prefix="blackjack_policy"):
    np.save(f"{filename_prefix}.npy", policy_table)
    np.savetxt(f"{filename_prefix}.csv", policy_table, fmt="%d", delimiter=",")
    with open(f"{filename_prefix}.h", "w") as f:
        f.write("const uint8_t blackjack_policy[22][2][11]={\n")
        for pt in range(22):
            f.write("  {")
            for ua in range(2):
                f.write("{" + ",".join(str(int(policy_table[pt, ua, tc])) for tc in range(11)) + "}")
                f.write("," if ua == 0 else "")
            f.write("},\n")
        f.write("};\n")
    print("✅ Policy exported successfully!")
