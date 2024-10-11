from collections import Counter

class HandEvaluator:
    def __init__(self):
        pass

    @staticmethod
    def hand_type(hand_rank):
        hand_types = ["High Card", "One Pair", "Two Pair", "Three of a Kind", "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"]
        return hand_types[hand_rank]

    @staticmethod
    def card_rank(card):
        rank = card.rank  # Access the rank attribute directly
        if rank == 'A':
            return 14
        elif rank == 'K':
            return 13
        elif rank == 'Q':
            return 12
        elif rank == 'J':
            return 11
        else:
            return int(rank)

    @staticmethod
    def card_suit(card):
        return card.suit  # Access the suit attribute directly

    @staticmethod
    def is_straight_flush(hand):
        suits = [HandEvaluator.card_suit(card) for card in hand]
        ranks = sorted([HandEvaluator.card_rank(card) for card in hand])
        return len(set(suits)) == 1 and ranks == list(range(min(ranks), min(ranks) + 5))

    @staticmethod
    def is_four_of_a_kind(hand):
        ranks = [HandEvaluator.card_rank(card) for card in hand]
        return 4 in Counter(ranks).values()

    @staticmethod
    def is_full_house(hand):
        ranks = [HandEvaluator.card_rank(card) for card in hand]
        counter = Counter(ranks).values()
        return 3 in counter and 2 in counter

    @staticmethod
    def is_flush(hand):
        suits = [HandEvaluator.card_suit(card) for card in hand]
        return len(set(suits)) == 1

    @staticmethod
    def is_straight(hand):
        ranks = sorted([HandEvaluator.card_rank(card) for card in hand])
        return ranks == list(range(min(ranks), min(ranks) + 5))

    @staticmethod
    def is_three_of_a_kind(hand):
        ranks = [HandEvaluator.card_rank(card) for card in hand]
        return 3 in Counter(ranks).values()

    @staticmethod
    def is_two_pair(hand):
        ranks = [HandEvaluator.card_rank(card) for card in hand]
        counter = Counter(ranks).values()
        return len([count for count in counter if count == 2]) == 2

    @staticmethod
    def is_one_pair(hand):
        ranks = [HandEvaluator.card_rank(card) for card in hand]
        return 2 in Counter(ranks).values()

    @staticmethod
    def best_hand(player_hand, community_cards):
        all_cards = player_hand + community_cards
        best = []
        best_rank = (0, [])

        for i in range(len(all_cards)):
            for j in range(i + 1, len(all_cards)):
                for k in range(j + 1, len(all_cards)):
                    for l in range(k + 1, len(all_cards)):
                        for m in range(l + 1, len(all_cards)):
                            hand = [all_cards[i], all_cards[j], all_cards[k], all_cards[l], all_cards[m]]
                            current_best_rank = (0, sorted(hand, key=lambda x: HandEvaluator.card_rank(x), reverse=True))

                            if HandEvaluator.is_straight_flush(hand):
                                current_best_rank = (8, sorted(hand, key=lambda x: HandEvaluator.card_rank(x), reverse=True))
                            elif HandEvaluator.is_four_of_a_kind(hand):
                                current_best_rank = (7, sorted(hand, key=lambda x: HandEvaluator.card_rank(x), reverse=True))
                            elif HandEvaluator.is_full_house(hand):
                                current_best_rank = (6, sorted(hand, key=lambda x: HandEvaluator.card_rank(x), reverse=True))
                            elif HandEvaluator.is_flush(hand):
                                current_best_rank = (5, sorted(hand, key=lambda x: HandEvaluator.card_rank(x), reverse=True))
                            elif HandEvaluator.is_straight(hand):
                                current_best_rank = (4, sorted(hand, key=lambda x: HandEvaluator.card_rank(x), reverse=True))
                            elif HandEvaluator.is_three_of_a_kind(hand):
                                current_best_rank = (3, sorted(hand, key=lambda x: HandEvaluator.card_rank(x), reverse=True))
                            elif HandEvaluator.is_two_pair(hand):
                                current_best_rank = (2, sorted(hand, key=lambda x: HandEvaluator.card_rank(x), reverse=True))
                            elif HandEvaluator.is_one_pair(hand):
                                current_best_rank = (1, sorted(hand, key=lambda x: HandEvaluator.card_rank(x), reverse=True))
                            else:
                                current_best_rank = (0, sorted(hand, key=lambda x: HandEvaluator.card_rank(x), reverse=True))

                            best_rank = max(best_rank, current_best_rank, key=lambda x: (x[0], [HandEvaluator.card_rank(card) for card in x[1]]))

        return best_rank
