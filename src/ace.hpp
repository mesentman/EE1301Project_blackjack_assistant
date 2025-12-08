#ifndef Ace_HPP
#define Ace_HPP

#include <vector>
#include <cmath>

// GENERIC: Counts total aces in a hand
// Logic: Checks if card index corresponds to an Ace (0, 13, 26, 39)
inline int CountAces(const std::vector<int>& cards){
    int ace_count = 0;
    for (int card : cards) {
        if (card % 13 == 0) { // Ace card
            ace_count++;
        }
    }
    return ace_count;
}

// GENERIC: Adjusts total if bust, using available soft aces
// Pass by reference (&) so it updates the variables directly
inline void AdjustForAces(int& count, int& softAceCount) {
    // Base Case: If we are under 21 OR we have no aces left to change, stop.
    if (count <= 21 || softAceCount == 0) {
        return;
    }

    // Recursive Step: We are over 21 and have an ace.
    count -= 10;       // Turn Ace (11) into Ace (1)
    softAceCount--;    // We used up one "Soft" Ace
    
    // Recurse to check if we still need to adjust
    AdjustForAces(count, softAceCount);
}

#endif // Ace_HPP