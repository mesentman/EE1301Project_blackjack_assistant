import numpy as np
import os
from datetime import datetime

def export_policy(policy_table, filename_prefix="blackjack_policy"):
    """
    Export a trained DQN policy table to multiple formats:
      - .npy for Python reloading
      - .csv for human inspection
      - .h for embedded C/C++ deployment
      - .txt for human-readable action names
    
    Args:
        policy_table: numpy array of shape [22, 2, num_count_bins]
        filename_prefix: base name for exported files
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
        f.write(f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("// Dimensions: [22][2][%d]\n" % shape[2])
        f.write("// Format: [player_total][usable_ace][true_count_bin]\n")
        f.write("// Actions: 0=HIT, 1=STAND, 2=DOUBLE, 3=SPLIT, 4=SURRENDER\n\n")
        f.write("#ifndef BLACKJACK_POLICY_H\n")
        f.write("#define BLACKJACK_POLICY_H\n\n")
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
        f.write("};\n\n")
        f.write("#endif // BLACKJACK_POLICY_H\n")

    # --- Save as human-readable text ---
    ACTION_NAMES = ["HIT", "STAND", "DOUBLE", "SPLIT", "SURRENDER"]
    with open(f"{base_path}.txt", "w") as f:
        f.write("=" * 80 + "\n")
        f.write("BLACKJACK POLICY TABLE (Human Readable)\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        shape = policy_table.shape
        for ua in range(2):
            ace_label = "WITH USABLE ACE" if ua == 1 else "NO USABLE ACE"
            f.write(f"\n{'=' * 80}\n")
            f.write(f"{ace_label}\n")
            f.write(f"{'=' * 80}\n")
            
            # Header row with true count bins
            f.write(f"{'Total':<8}")
            for tc in range(shape[2]):
                tc_value = tc - abs(-5)  # Assuming COUNT_BINS starts at -5
                f.write(f"TC{tc_value:+3d} ")
            f.write("\n" + "-" * 80 + "\n")
            
            # Policy for each total
            for pt in range(4, 22):
                f.write(f"{pt:<8}")
                for tc in range(shape[2]):
                    action_idx = int(policy_table[pt, ua, tc])
                    action_name = ACTION_NAMES[action_idx] if action_idx < len(ACTION_NAMES) else "???"
                    f.write(f"{action_name:<5}")
                f.write("\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("Action Codes: 0=HIT, 1=STAND, 2=DOUBLE, 3=SPLIT, 4=SURRENDER\n")
        f.write("=" * 80 + "\n")

    print(f"[✅] Exported policy to:")
    print(f"    - {base_path}.npy (NumPy array)")
    print(f"    - {base_path}.csv (CSV format)")
    print(f"    - {base_path}.h (C header)")
    print(f"    - {base_path}.txt (Human readable)")