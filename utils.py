import numpy as np

def export_policy(policy_table, filename_prefix="blackjack_policy"):
    # Save as .npy (3D works fine)
    np.save(f"{filename_prefix}.npy", policy_table)

    # Save as CSV: flatten 2nd & 3rd dims
    reshaped = policy_table.reshape(22, -1)  # shape becomes (22, 2*11=22)
    np.savetxt(f"{filename_prefix}.csv", reshaped, fmt="%d", delimiter=",")

    # Save as C header
    with open(f"{filename_prefix}.h", "w") as f:
        f.write(f"const uint8_t blackjack_policy[22][2][{policy_table.shape[2]}] = {{\n")
        for pt in range(22):
            f.write("  {")
            for ua in range(2):
                f.write("{" + ",".join(str(int(policy_table[pt, ua, tc])) for tc in range(policy_table.shape[2])) + "}")
                if ua == 0: f.write(",")
            f.write("},\n")
        f.write("};\n")
