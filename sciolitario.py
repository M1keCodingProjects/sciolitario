from re     import search
from enum   import StrEnum
from random import shuffle
from typing import Optional, Self

class Suit(StrEnum):
    Spades   = '♤'
    Hearts   = '♡'
    Diamonds = '♢'
    Clubs    = '♧'

type Rank = int
def intoRank(n:int) -> Rank:
    if n < 1 or n > 10: raise ValueError(f"A Rank must be between 1 and 10, got {n} instead.")

    return n

class Card:
    TOP        = "┌───┐"
    BOTTOM     = "└───┘"
    FACES      = "JQK"
    FACE_NAMES = ("Jack", "Queen", "King")

    def __init__(self, suit:Suit, rank:Rank) -> None:
        self.suit      = suit
        self.rank      = rank

        self.name      = self._getRankStr(asSymbol = False) + " of " + suit.name
        self.isCovered = True
    
    def canPair(self, card:Self) -> bool: return self.rank + card.rank == 10

    def _getRankStr(self, *, asSymbol = True) -> str:
        return str(self.rank) if self.rank < 8 else (Card.FACES if asSymbol else Card.FACE_NAMES)[self.rank - 8]

    def getCardLayers(self:Optional[Self]) -> tuple[str, str, str, str]:
        if not self: return ("     ", ) * 4

        cardInfo = "?¿" if self.isCovered else (self._getRankStr(), self.suit)
        return Card.TOP, f"│ {cardInfo[0]} │", f"│ {cardInfo[1]} │", Card.BOTTOM

    def print(self) -> None: print('\n'.join(self.getCardLayers()))

# TODO: add possibility to select top 2 from pile
class Deck:
    class DrawEmptyErr(Exception):
        def __init__(self):
            super().__init__("Attempted to draw a card from an empty deck.")

    def __init__(self, *, filled = False) -> None:
        self.cards :list[Card] = []
        if not filled: return

        for suit in Suit:
            for rank in range(1, 11):
                self.cards.append(Card(suit, rank))
        
        shuffle(self.cards)

    def put(self, card:Card) -> None:
        self.cards.append(card)
    
    def draw(self) -> Card:
        try: card = self.remove()
        except IndexError: raise Deck.DrawEmptyErr()

        card.isCovered = False
        return card

    def remove(self) -> Card: return self.cards.pop() 

    def select(self, suit:Suit, rank:Rank) -> Optional[Card]:
        topCard = self.cards[-1]
        return topCard if topCard.suit == suit and topCard.rank == rank else None

    def print(self) -> None:
        self.cards[-1].print() if self.cards else print("┌   ┐\n\n\n└   ┘")

class Table:
    def __init__(self, deck:Deck, nRows = 6):
        self.nRows = nRows

        self.nCards = Table._getCombinations(self.nRows) + self.nRows
        self.cards = {(card.suit, card.rank) : card for card in deck.cards[:self.nCards]}

        for card in deck.cards[self.nCards - self.nRows:self.nCards]: card.isCovered = False
        del deck.cards[:self.nCards]

        self.lastRowExists = True
    
    @staticmethod
    def _getCombinations(n:int) -> int: return (n + 1) * n // 2

    def select(self, suit:Suit, rank:Rank) -> Card:
        card = self.cards.get((suit, rank))
        return None if not card or card.isCovered else card

    def remove(self, card:Card) -> None:
        cards          = list(self.cards.values())
        removedCardPos = cards.index(card)
        
        y = int((-1 + (1 + 8 * removedCardPos) ** 0.5) // 2)
        x = removedCardPos - Table._getCombinations(y)
        
        leftCovered  = cards[removedCardPos - y - 1]
        rightCovered = cards[removedCardPos - y]

        if self.lastRowExists and y == self.nRows:
            rightCovered.isCovered = False # Last line behaves differently
        else:
            # leftmost card can't check leftCovered:
            if x and not cards[removedCardPos - 1]: leftCovered.isCovered = False

            # rightmost card can't check rightCovered:
            if x < y and not cards[removedCardPos + 1]: rightCovered.isCovered = False

        cards[removedCardPos]              = None
        self.cards[(card.suit, card.rank)] = None

        # Remove unused cards:
        if list(filter(None, cards[self.nCards - self.nRows:self.nCards])): return
        
        self.nCards -= self.nRows
        if self.lastRowExists: self.lastRowExists = False
        else: self.nRows -= 1

    def _getRowLayer(self, y:int, layers:tuple[str, ...]) -> str:
        return ' ' * (3 * (self.nRows - y - 1)) + ' '.join(layers)

    def print(self) -> None:
        cards = list(self.cards.values())
        
        for y in range(self.nRows):
            rowBuff = ""
            startId = Table._getCombinations(y)

            i = 0
            for layers in zip(*map(Card.getCardLayers, cards[startId:startId + y + 1])):
                rowBuff += bool(i) * '\n' + self._getRowLayer(y, layers)
                i += 1
            
            print(rowBuff)

        if self.lastRowExists:
            print('\n'.join(map(' '.join, zip(*map(Card.getCardLayers, cards[-self.nRows:])))))

class GameManager:
    class InvalidCardErr(Exception):
        def __init__(self, cardInpt:str, details = "") -> None:
            super().__init__("Invalid card selection" +
                f": {details}" * bool(details) +
                f", got \"{cardInpt}\" instead.")

    class InvalidPairErr(Exception):
        DEF_DETAILS = "the ranks add up to {}, not 10"
        def __init__(self, first:Card, second:Card, details = DEF_DETAILS) -> None:
            super().__init__(f"Invalid pair attempt between {first.name} and {second.name}, {details.format(first.rank + second.rank)}.")

    def __init__(self) -> None:
        self.deck  = Deck(filled = True)
        self.pile  = Deck()
        self.comp  = Deck()
        self.table = Table(self.deck)
    
    def run(self) -> None:
        self.show()
        try:
            while True:
                self.update()
                self.show()
        
        except Deck.DrawEmptyErr: print("The deck is empty! You loose.")
    
    def update(self) -> None:
        while True:
            match input("Would you like to: draw & discard (d) or pair 2 cards (p)? ").lower().strip():
                case 'd':
                    self.drawAndDiscard()
                    break
                
                case 'p':
                    try:
                        self.pairCards()
                        break

                    except (GameManager.InvalidCardErr, GameManager.InvalidPairErr) as err: print(err)
                
                case _  :
                    print("Invalid action, input either 'd' or 'p'.")

    def drawAndDiscard(self) -> None:
        self.pile.put(self.deck.draw())

    def _removeCard(self, card:Card) -> None:
        self.pile.remove() if self.pile.cards and self.pile.cards[-1] is card else self.table.remove(card)
        self.comp.put(card)
        card.isCovered = True

    def pairCards(self) -> None:
        if (first := self.selectCard()).rank == 10:
            self._removeCard(first)
            # TODO: win condition
            return

        second = self.selectCard()
        if not first.canPair(second): raise GameManager.InvalidPairErr(first, second)
        if first is second: raise GameManager.InvalidPairErr(first, second, "cannot pair a card with itself")

        self._removeCard(first)
        self._removeCard(second)

        #TODO: win condition
    
    def selectCard(self) -> Card:
        # TODO: allow selection with J, Q or K
        userInpt = input("Insert rank (1-10) and suit (H, S, C or D) of selected card: ").strip()
        patMatch = search(r"^(\d\d?|j|q|k) ?(h|s|c|d)$", userInpt.lower())

        if not patMatch: raise GameManager.InvalidCardErr(userInpt, "could not identify valid suit and rank")

        if (rank := patMatch.group(1)).isalpha(): rank = 8 + Card.FACES.find(rank.upper())
        else:
            try: rank = intoRank(int(rank))
            except ValueError as err: raise GameManager.InvalidCardErr(userInpt, str(err))

        suit = Suit[Suit._member_names_["shdc".find(patMatch.group(2))]]
        if card := self.pile.cards and self.pile.select(suit, rank) or self.table.select(suit, rank):
            return card

        raise GameManager.InvalidCardErr(userInpt, "The selected card is not available")

    def show(self) -> None:
        self.table.print()

        print(f"\nCards in deck: {len(self.deck.cards)}")
        self.deck.print()

        print(f"\nDiscarded cards: {len(self.pile.cards)}")
        self.pile.print()

        print(f"\nCompleted cards: {len(self.comp.cards)}")
        self.comp.print()

if __name__ == "__main__":
    GameManager().run()