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

    def isExactly(self, suit:Suit, rank:Rank) -> bool:
        return self.suit == suit and self.rank == rank

    def _getRankStr(self, *, asSymbol = True) -> str:
        return str(self.rank) if self.rank < 8 else (Card.FACES if asSymbol else Card.FACE_NAMES)[self.rank - 8]

    def getCardLayers(self:Optional[Self]) -> tuple[str, str, str, str]:
        if not self: return ("     ", ) * 4

        cardInfo = "?¿" if self.isCovered else (self._getRankStr(), self.suit)
        return Card.TOP, f"│ {cardInfo[0]} │", f"│ {cardInfo[1]} │", Card.BOTTOM

    def print(self) -> None: print('\n'.join(self.getCardLayers()))

class Deck:
    EMPTY = "┌   ┐\n\n\n└   ┘"

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
        try: card = self.cards.pop()
        except IndexError: raise Deck.DrawEmptyErr()

        card.isCovered = False
        return card

    def remove(self, card:Card) -> bool:
        return bool(self.cards.pop()) if self.cards and card is self.cards[-1] else False

    def select(self, suit:Suit, rank:Rank) -> Optional[Card]:
        if not self.cards: return None

        topCard = self.cards[-1]
        return topCard if topCard.isExactly(suit, rank) else None

    def print(self) -> None:
        self.cards[-1].print() if self.cards else print(Deck.EMPTY)

class DiscardPile(Deck):
    def remove(self, card:Card) -> Optional[Card]:
        if not self.cards: return False

        if card is self.cards[-1]: self.cards.pop()
        elif len(self.cards) > 1 and card is self.cards[-2]: self.cards.pop(-2)
        else: return False

        return True

    def select(self, suit:Suit, rank:Rank) -> Optional[Card]:
        if topCard := super().select(suit, rank): return topCard
        if len(self.cards) < 2: return None

        nextCard = self.cards[-2]
        return nextCard if nextCard.isExactly(suit, rank) else None

    def print(self) -> None:
        if not self.cards:
            print(Deck.EMPTY)
            return
        
        topCardLayers  = self.cards[-1].getCardLayers()
        nextCardLayers = self.cards[-2].getCardLayers() if len(self.cards) > 1 else Deck.EMPTY.split('\n')

        buff = topCardLayers[0] + '\n'
        for i in range(1, 4): buff += topCardLayers[i] + nextCardLayers[i - 1][-3:] + '\n'
        print(buff + "   " + nextCardLayers[-1])

class Table:
    LAYER_SEP = ('¿', Card.BOTTOM[1], ' ')

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

    def print(self) -> None:
        buff    = ""
        startId = 0
        cards   = list(self.cards.values())
        for y in range(self.nRows):
            leftPad = ' ' * (3 * (self.nRows - y - 1))
            row     = cards[startId:startId + y + 1]
            layer0  = leftPad
            layer1  = leftPad
            for x, card in enumerate(row):
                isRightmost = x == y
                if card: # Here you know at least 1 card is covering the one above
                    layers  = card.getCardLayers()
                    layer0 += layers[0] + Table.LAYER_SEP[0] * (not isRightmost)
                    layer1 += layers[1] + Table.LAYER_SEP[1] * (not isRightmost)
                    continue
            
                if not y: continue

                isLeftmost  = not x
                leftCovered  = Card.getCardLayers(cards[startId + x - y - 1])
                rightCovered = Card.getCardLayers(cards[startId + x - y])

                layer0 += ("  " if isLeftmost else leftCovered[2][3:]) + Table.LAYER_SEP[2] + ("   " if isRightmost else rightCovered[2][:3])
                layer1 += ("  " if isLeftmost else leftCovered[3][3:]) + Table.LAYER_SEP[2] + ("   " if isRightmost else rightCovered[3][:3])
            
            buff    += layer0 + '\n' + layer1 + '\n'
            startId += y + 1
        
        # Either we draw the special case row or finish the last row
        layers = [leftPad] * (2 + 2 * self.lastRowExists)
        for x, card in enumerate(cards[-self.nRows:]):
            cardLayers = Card.getCardLayers(card)
            cardAbove  = row[x]
            
            if not card: cardLayers = Card.getCardLayers(cardAbove)[-2:] + cardLayers[-2:]
            for i in range(2 + 2 * self.lastRowExists): layers[i] += cardLayers[i] + Table.LAYER_SEP[2]

        print(buff + '\n'.join(layers))

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
        self.pile  = DiscardPile()
        self.comp  = Deck()
        self.table = Table(self.deck)

        self.isPile2ndSelected = False
    
    def run(self) -> None:
        self.show()
        try:
            while self.table.nRows:
                self.update()
                self.show()
        
        except Deck.DrawEmptyErr:
            print("The deck is empty! You loose.")
            return

        print("The table is empty! You win.")
    
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
        self.pile.remove(card) or self.table.remove(card)
        self.comp.put(card)
        card.isCovered = True

    def pairCards(self) -> None:
        self.isPile2ndSelected = False
        if (first := self.selectCard()).rank == 10:
            if self.isPile2ndSelected: raise GameManager.InvalidCardErr(
                first.name, "cannot select discarded cards below the top")
            
            self._removeCard(first)
            return

        firstIsPile2nd = self.isPile2ndSelected

        second = self.selectCard()
        if not first.canPair(second): raise GameManager.InvalidPairErr(first, second)
        if first is second: raise GameManager.InvalidPairErr(first, second, "cannot pair a card with itself")
        
        if firstIsPile2nd: # 2nd check should only be done if first card is not pile 2nd
            if second is not self.pile.cards[-1]: raise GameManager.InvalidCardErr(
                first.name, "cannot select discarded cards below the top")
        
        elif self.isPile2ndSelected and first is not self.pile.cards[-1]:
            raise GameManager.InvalidCardErr(second.name, "cannot select discarded cards below the top")

        self._removeCard(first)
        self._removeCard(second)
    
    def selectCard(self) -> Card:
        userInpt = input("Insert rank (1-10) and suit (H, S, C or D) of selected card: ").strip()
        patMatch = search(r"^(\d\d?|j|q|k) ?(h|s|c|d)$", userInpt.lower())

        if not patMatch: raise GameManager.InvalidCardErr(userInpt, "could not identify valid suit and rank")

        suit = Suit[Suit._member_names_["shdc".find(patMatch.group(2))]]
        if (rank := patMatch.group(1)).isalpha(): rank = 8 + Card.FACES.find(rank.upper())
        else:
            try: rank = intoRank(int(rank))
            except ValueError as err: raise GameManager.InvalidCardErr(userInpt, str(err))

        if card := self.pile.select(suit, rank): # condition split for length
            if len(self.pile.cards) > 1 and card is self.pile.cards[-2]: self.isPile2ndSelected = True
        
        if not card: card = self.table.select(suit, rank)
        if card: return card

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