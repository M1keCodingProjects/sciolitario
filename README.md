# Solitaire game
Welcome to solitaire! Your goal is to clear the **table** by making **pairs**.
Any **2 cards** with ranks adding up to exactly **10** can form a pair.

Rank values are the card numbers; for **face cards** refer to this:
|Face  |Rank|
|------|----|
|Jacks |8   |
|Queens|9   |
|Kings |10  |
|Aces  |1   |

The deck is a standard **40**-cards european deck, so no jokers.

## Game user input actions
**Draw** & discard from deck to pile with ```d```, the card at the **top** of the pile can be used in pairing.
You can also pair the **top 2** cards of the discard pile together.
Specify cards to **pair** as ```RS RS```, where:
- ```R``` is the **rank** (1-10 or J, Q, K, A)
- ```S``` is the **suit**: H for Hearts(♡), S for Spades(♤), C for Clubs(♧) and D for Diamonds(♢)

Good luck!

## Installing
Downloading and running the ```sciolitario.py``` file is sufficient.
