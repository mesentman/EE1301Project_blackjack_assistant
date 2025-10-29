import numpy as np
import os

def export_policy(policy_table, filename_prefix="blackjack_policy"):
    """
    Export a trained DQN policy table to multiple formats:
      - .npy for Python reloading
      - .csv for human inspection
      - .h for embedded C/C++ deployment
    """
    os.makedirs("exports", exist_ok=True)
    base_path = os.path.join("exports", filename_prefix)

    # --- Save as .npy ---
    np.save(f"{base_path}.npy", policy_table)

    # --- Save as .csv ---
    reshaped = policy_table.reshape(22, -1)
    np.savetxt(f"{base_path}.csv", reshaped, fmt="%d", delimiter=",")

    # --- Save as C header ---
    with open(f"{base_path}.h", "w") as f:
        shape = policy_table.shape
        f.write("// Auto-generated Blackjack Policy Table\n")
        f.write("// Dimensions: [22][2][%d]\n\n" % shape[2])
        f.write("#include <stdint.h>\n\n")
        f.write(f"const uint8_t blackjack_policy[22][2][{shape[2]}] = {{\n")
        for pt in range(22):
            f.write("  {")
            for ua in range(2):
                values = ",".join(str(int(policy_table[pt, ua, tc])) for tc in range(shape[2]))
                f.write("{" + values + "}")
                if ua == 0:
                    f.write(",")
            f.write("},\n")
        f.write("};\n")

    print(f"[✅] Exported policy to '{base_path}.npy', '.csv', and '.h'")
