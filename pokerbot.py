from misc.deck import Deck
from misc.hand_evaluator import HandEvaluator
import time
import random
from collections import Counter
import misc.ansicolors as colors

deck = Deck()

def shuffle_deal(deck):
    player1_hand = deck.deal(2)
    player2_hand = deck.deal(2)
    return player1_hand, player2_hand, deck

class Player:
    def __init__(self, name, chips):
        self.name = name
        self.chips = chips
        self.hand = []
        self.current_bet = 0
        self.folded = False

    def bet(self, amount):
        self.chips -= amount
        self.current_bet += amount

    def fold(self):
        self.folded = True

    def check(self):
        pass

    def call(self, hero_bet, villain_bet):
        call_amount = villain_bet - hero_bet
        self.bet(call_amount)
        return call_amount

    def raise_bet(self, villain):
        invalid_value = True
        while invalid_value:
            raise_input = input(f"{colors.MAGENTA}Enter raise amount (enter 'all in' to go all in): {colors.RESET}")
            if raise_input.lower() == "all in":
                invalid_value = False
            elif raise_input.isdigit() and int(raise_input) >= 2 * villain.current_bet:
                invalid_value = False
            else:
                print(f"{colors.RED}Invalid input. You must bet at least twice the opponent's bet ({villain.current_bet}), so min raise is {villain.current_bet * 2}{colors.RESET}")
        
        if raise_input.lower() == "all in":
            if self.chips > villain.chips:
                print(f"{self.name}{colors.MAGENTA} has gone all in. Since {colors.RESET}{villain.name}{colors.MAGENTA} has less chips, the all in amount is set at {colors.RESET}{villain.name}{colors.MAGENTA}'s stack, so {colors.RESET}{self.name}{colors.MAGENTA} goes all in for {villain.chips}.{colors.RESET}")
                raise_amount = villain.chips + (villain.current_bet - self.current_bet)
            else:
                raise_amount = self.chips
        else:
            raise_amount = int(raise_input)
        
        self.bet(raise_amount)
        return raise_amount

class AIPlayer(Player):
    def __init__(self, name, chips):
        super().__init__(name, chips)

    def evaluate_hand_strength(self, community_cards):
        evaluator = HandEvaluator()
        best_hand = evaluator.best_hand(self.hand, community_cards)
        hand_rank = best_hand[0]
        return hand_rank

    def pot_odds(self, call_amount, pot):
        return call_amount / (pot + call_amount)

    def expected_value(self, hand_strength, pot, call_amount):
        return hand_strength * pot - call_amount
    
    def calc_outs(self, hand, community_cards):
        outs = 0
        evaluator = HandEvaluator()

        # Flush Draw
        suits = [card.suit for card in hand + community_cards]
        for suit in set(suits):
            if suits.count(suit) == 4:
                outs += 9  # 13 total of a suit minus 4 known cards
        
        # Straight draw
        ranks = sorted(set([evaluator.card_rank(card) for card in hand + community_cards]))
        for i in range(len(ranks) - 3):
            if ranks[i+3] - ranks[i] == 3:
                outs += 8  # Straight draw, 4 cards can complete either end
        
        unseen_cards = 52 - len(hand) - len(community_cards)
        
        # Odds of hitting an out on the next card
        odds_per_card = outs / unseen_cards
        # If the draw is on the turn, the player has two chances (turn + river)
        odds = 1 - ((1 - odds_per_card) ** 2)
        
        return odds * 100

    def board_texture(self, community_cards):
        evaluator = HandEvaluator()

        if len(community_cards) < 3: # Pre-flop
            return "safe"

        # Flush
        suits = [card.suit for card in community_cards]
        suit_counts = Counter(suits)
        max_suit_count = max(suit_counts.values())

        # Straight
        ranks = sorted(set([evaluator.card_rank(card) for card in community_cards]))
        is_straight_draw = any(ranks[i + 2] - ranks[i] <= 4 for i in range(len(ranks) - 2))

        # Dangerous if there are 4+ cards of the same suit or 4+ cards in a sequence
        if max_suit_count >= 4 or (len(ranks) >= 4 and any(ranks[i + 3] - ranks[i] <= 4 for i in range(len(ranks) - 3))):
            return "dangerous"
        
        # Dangerous if there are 2 or more cards of the same rank (potential pair on the board)
        rank_counts = Counter(ranks)
        if any(count >= 2 for count in rank_counts.values()):
            return "dangerous"

        # Flush draw (3 cards of the same suit)
        if max_suit_count == 3:
            return "flush_draw"

        # Straight draw (3 cards forming a 5-card sequence)
        if is_straight_draw:
            return "straight_draw"

        return "safe"
        
    def simulate_hand(self, bot_hand, community_cards, num_simulations=1000):
        deck = Deck()
        evaluator = HandEvaluator()
        bot_wins = 0
        
        for _ in range(num_simulations):
            deck = Deck()  # Reset the deck each time
            deck.cards = [card for card in deck.cards if card not in bot_hand]
            cc = community_cards
            opponent_hand = deck.deal(2)
            
            num_cc = len(community_cards)
            if num_cc == 0:
                cc = deck.deal(5)
            elif num_cc == 3:
                cc = community_cards + deck.deal(2)
            else:
                cc = community_cards + deck.deal(1)

            bot_best_hand = evaluator.best_hand(bot_hand, cc)
            opponent_best_hand = evaluator.best_hand(opponent_hand, cc)

            if bot_best_hand[0] > opponent_best_hand[0]:
                bot_wins += 1
            elif bot_best_hand[0] == opponent_best_hand[0]:

                bot_high_cards = [evaluator.card_rank(card) for card in bot_best_hand[1]]
                opponent_high_cards = [evaluator.card_rank(card) for card in opponent_best_hand[1]]
                
                if bot_high_cards > opponent_high_cards:
                    bot_wins += 1
                elif bot_high_cards == opponent_high_cards:
                    bot_wins += 0.5  # Count tie as half win
        
        win_percentage = bot_wins / num_simulations
        return win_percentage

    def make_decision(self, community_cards, pot, opponent_bet, type):
        call_amount = opponent_bet - self.current_bet
        raise_probability = aggressiveness
        board_type = self.board_texture(community_cards)
        print(board_type)
        hand_strength = self.simulate_hand(self.hand, community_cards, num_simulations=1000)
        print(f"HS: {hand_strength}")
        ev = self.expected_value(hand_strength, pot, call_amount)
        print(f"EV: {ev}")
        outs = self.calc_outs(self.hand, community_cards)
        pot_odds = self.pot_odds(call_amount, pot)
        print(f"PO: {pot_odds}")

        time.sleep(1)

        if type == 2:  # Being taken all in; call/fold scenario
            if hand_strength > 0.75:
                return "call"
            elif pot_odds > hand_strength and ev > 0:
                return "call" if random.random() < raise_probability else "fold"
            else:
                return "fold"
        
        elif type == 3 or type == 1:  # 1: Bets equal: check, raise | 3: General scenario: call, raise, or fold
            if board_type == "dangerous":
                if hand_strength > 0.7 and ev > 0:  # Only raise with stronger hands on dangerous boards
                    if random.random() < raise_probability:
                        return "raise"
                    else:
                        if type == 1:
                            return "check"
                        else:
                            return "call"
                else:
                    if type == 1:
                        return "check"
                    else:
                        return "fold"

            elif board_type == "safe":
                if hand_strength > 0.5 or (pot_odds > 0.2 and ev > 0):
                    if hand_strength > 0.5 and random.random() < raise_probability:
                        return "raise"
                    else:
                        if type == 1:
                            return "check"
                        else:
                            return "call"
                else:
                    if type == 1:
                        return "check"
                    else:
                        return "fold"
                
            else:  # Draw-heavy board
                if hand_strength > 0.55 and pot_odds > hand_strength:  # Raise more selectively on draw-heavy boards
                    if random.random() < raise_probability:
                        return "raise"
                    else:
                        if type == 1:
                            return "check"
                        else:
                            return "call"
                else:
                    if type == 1:
                        return "check"
                    else:
                        return "fold"


    def bot_raise(self, opponent):
        hand_strength = self.simulate_hand(self.hand, community_cards, num_simulations=1000)
        agg = aggressiveness

        if hand_strength + agg > 1.2: # Very strong hand
            base_multiplier = random.randint(3, 5)
            scaling_factor = (random.randint(15, 20))/10
        elif hand_strength + agg > 1.0:  # Moderate hand
            base_multiplier = random.randint(1, 3)
            scaling_factor = (random.randint(10, 15))/10
        else:  # Weak hand
            base_multiplier = random.randint(1, 2)
            scaling_factor = (random.randint(5, 10))/10

        chosen_multiplier = base_multiplier * scaling_factor

        base_raise = round((SMALL_BLIND * chosen_multiplier),2)
        br = max(base_raise, 2 * opponent.current_bet)
        br = min(br, self.chips)  # Ensure the bot doesn’t bet more than it has
        br = round(br, 1)
        br = round(br * 2) / 2

        self.bet(br)
        return br

def display_game_state(player1, player2, pot, community_cards, flip):
    evaluator = HandEvaluator()
    print(f"{colors.CYAN}\n--- Game State ---{colors.RESET}")
    if flip:
        print(f"{player1.name}{colors.CYAN}'s Hand:{colors.RESET} {player1.hand}")
        print(f"{player2.name}{colors.CYAN}'s Hand:{colors.RESET} {player2.hand}")
    else:
        if not isinstance(player1, AIPlayer):
            print(f"{player1.name}{colors.CYAN}'s Hand:{colors.RESET} {player1.hand}")
            print(f"{colors.CYAN}Hand Strength:{colors.RESET} {evaluator.hand_type((evaluator.best_hand(player1.hand, community_cards))[0])}")
        else:
            print(f"{player2.name}{colors.CYAN}'s Hand:{colors.RESET} {player2.hand}")
            print(f"{colors.CYAN}Hand Strength:{colors.RESET} {evaluator.hand_type((evaluator.best_hand(player2.hand, community_cards))[0])}")
    print(f"{colors.CYAN}Community Cards:{colors.RESET} {community_cards}")
    print(f"{colors.CYAN}Pot Size:{colors.RESET} {pot}")
    print(f"{player1.name}{colors.CYAN} Chips:{colors.RESET} {player1.chips}")
    print(f"{player2.name}{colors.CYAN} Chips:{colors.RESET} {player2.chips}")
    print(f"{colors.CYAN}------------------\n{colors.RESET}")

def betting_round(player1, player1_bet, player2, player2_bet, pot, blinds):
    if (not player1.folded and not player2.folded) and (player1.chips > 0 and player2.chips > 0):
        player1_acted = False
        player2_acted = False
        player1.current_bet = player1_bet
        player2.current_bet = player2_bet
        while True:
            # Player 1's turn
            if not player1_acted:
                while True:
                    if player1.current_bet == player2.current_bet:
                        if isinstance(player1, AIPlayer):
                            action = player1.make_decision(community_cards, pot, player2.current_bet, 1)
                            break
                        else:
                            action = input(f"{player1.name}{colors.CYAN}, choose your action (check, raise): {colors.RESET}").lower()
                            if action in ['check', 'raise']:
                                break
                            else:
                                print(f"{colors.RED}Invalid action. Please choose 'check' or 'raise'.{colors.RESET}")
                    elif player2.current_bet >= player1.chips:
                        if isinstance(player1, AIPlayer):
                            action = player1.make_decision(community_cards, pot, player2.current_bet, 2)
                            break
                        else:
                            action = input(f"{player1.name}{colors.MAGENTA}, choose your action (call {player2.current_bet - player1.current_bet}, fold): {colors.RESET}").lower()
                            if action in ['call', 'fold']:
                                break
                            else:
                                print(f"{colors.RED}Invalid action. Please choose 'call' or 'fold'.{colors.RESET}")
                    else:
                        if isinstance(player1, AIPlayer):
                            action = player1.make_decision(community_cards, pot, player2.current_bet, 3)
                            break
                        else:
                            action = input(f"{player1.name}{colors.MAGENTA}, choose your action (call {player2.current_bet - player1.current_bet}, raise, fold): {colors.RESET}").lower()
                            if action in ['call', 'raise', 'fold']:
                                break
                            else:
                                print(f"{colors.RED}Invalid action. Please choose 'call', 'raise', or 'fold'.{colors.RESET}")

                if action == 'fold':
                    print(f"{player1.name}{colors.GREEN} has folded.{colors.RESET}")
                    player1.fold()
                    player1_acted = True
                    break
                elif action == 'check':
                    print(f"{player1.name}{colors.GREEN} has checked.{colors.RESET}")
                    player1.check()
                    player1_acted = True
                elif action == 'call':
                    call_amount = player1.call(player1.current_bet, player2.current_bet)
                    print(f"{player1.name}{colors.GREEN} has called {call_amount}.{colors.RESET}")
                    pot += call_amount
                    player1_acted = True
                    if not blinds:
                        player2_acted = True
                elif action == 'raise':
                    if isinstance(player1, AIPlayer):
                        raise_amount = player1.bot_raise(player2)
                    else:
                        raise_amount = player1.raise_bet(player2)
                    print(f"{player1.name}{colors.GREEN} has raised {raise_amount}.{colors.RESET}")
                    pot += raise_amount
                    player1_acted = True
                    player2_acted = False
                        
            # Player 2's turn
            if not player2_acted:
                while True:
                    if player2.current_bet == player1.current_bet:
                        if isinstance(player2, AIPlayer):
                            action = player2.make_decision(community_cards, pot, player1.current_bet, 1)
                            break
                        else:
                            action = input(f"{player2.name}{colors.MAGENTA}, choose your action (check, raise): {colors.RESET}").lower()
                            if action in ['check', 'raise']:
                                break
                            else:
                                print(f"{colors.RED}Invalid action. Please choose 'check' or 'raise'.{colors.RESET}")
                    elif player1.current_bet >= player2.chips:
                        if isinstance(player2, AIPlayer):
                            action = player2.make_decision(community_cards, pot, player1.current_bet, 2)
                            break
                        else:
                            action = input(f"{player2.name}{colors.MAGENTA}, choose your action (call {player1.current_bet - player2.current_bet}, fold): {colors.RESET}").lower()
                            if action in ['call', 'fold']:
                                break
                            else:
                                print(f"{colors.RED}Invalid action. Please choose 'call' or 'fold'.{colors.RESET}")
                    else:
                        if isinstance(player2, AIPlayer):
                            action = player2.make_decision(community_cards, pot, player1.current_bet, 3)
                            break
                        else:
                            action = input(f"{player2.name}{colors.MAGENTA}, choose your action (call {player1.current_bet - player2.current_bet}, raise, fold): {colors.RESET}").lower()
                            if action in ['call', 'raise', 'fold']:
                                break
                            else:
                                print(f"{colors.RED}Invalid action. Please choose 'call', 'raise', or 'fold'.{colors.RESET}")

                if action == 'fold':
                    print(f"{player2.name}{colors.GREEN} has folded.{colors.RESET}")
                    player2.fold()
                    player2_acted = True
                    break
                elif action == 'check':
                    print(f"{player2.name}{colors.GREEN} has checked.{colors.RESET}")
                    player2.check()
                    player2_acted = True
                elif action == 'call':
                    call_amount = player2.call(player2.current_bet, player1.current_bet)
                    print(f"{player2.name}{colors.GREEN} has called {call_amount}.{colors.RESET}")
                    pot += call_amount
                    player2_acted = True
                    if not blinds:
                        player1_acted = True
                elif action == 'raise':
                    if isinstance(player2, AIPlayer):
                        raise_amount = player2.bot_raise(player1)
                    else:
                        raise_amount = player2.raise_bet(player1)
                    print(f"{player2.name}{colors.GREEN} has raised {raise_amount}.{colors.RESET}")
                    pot += raise_amount
                    player2_acted = True
                    player1_acted = False

            # End the betting round if both players have acted and bets are equal
            if player1_acted and player2_acted and player1.current_bet == player2.current_bet:
                break

    return pot

def compare_hands(hand1, hand2, community_cards):
    evaluator = HandEvaluator()
    best_hand1 = evaluator.best_hand(hand1, community_cards)
    best_hand2 = evaluator.best_hand(hand2, community_cards)

    print(f"{player1.name}{colors.CYAN} Best Hand: {best_hand1}{colors.RESET}")
    print(f"{player2.name}{colors.CYAN} Best Hand: {best_hand2}{colors.RESET}")

    hand_type1 = evaluator.hand_type(best_hand1[0])
    hand_type2 = evaluator.hand_type(best_hand2[0])

    if best_hand1[0] > best_hand2[0]:
        print(f"{player1.name}{colors.CYAN}'s {hand_type1} beats {colors.RESET}{player2.name}{colors.CYAN}'s {hand_type2}{colors.RESET}")
        return player1
    elif best_hand1[0] < best_hand2[0]:
        print(f"{player2.name}{colors.CYAN}'s {hand_type2} beats {colors.RESET}{player1.name}{colors.CYAN}'s {hand_type1}{colors.RESET}")
        return player2
    else:
        # Compare the card ranks in the best hands
        for card1, card2 in zip(best_hand1[1], best_hand2[1]):
            rank1 = evaluator.card_rank(card1)
            rank2 = evaluator.card_rank(card2)
            if rank1 > rank2:
                print(f"{player1.name}{colors.CYAN}'s {hand_type1} beats {colors.RESET}{player2.name}{colors.CYAN}'s {hand_type2}{colors.RESET}")
                return player1
            elif rank1 < rank2:
                print(f"{player2.name}{colors.CYAN}'s {hand_type2} beats {colors.RESET}{player1.name}{colors.CYAN}'s {hand_type1}{colors.RESET}")
                return player2
        print(f"{colors.CYAN}It's a tie{colors.RESET}")
        return

# --- MAIN GAME STATE ---
while True:
    buyin = int(input(f"{colors.BLUE}How much would you like to buy in? This determines the blinds of the game as well: {colors.RESET}"))
    if isinstance(buyin, int):
        break
    else:
        print(f"{colors.RED}Invalid entry. Try again.{colors.RESET}")
SMALL_BLIND = buyin/100
BIG_BLIND = buyin/50
print (f"{colors.CYAN}Blinds are {SMALL_BLIND}/{BIG_BLIND}.{colors.RESET}")
while True:
    aggressiveness = int(input(f"{colors.BLUE}On a scale of 1 to 10, how aggressive do you want the bot do be? (5/6 Recommended): {colors.RESET}"))
    if aggressiveness in range(1, 11):
        aggressiveness /= 10
        break
    else:
        print(f"{colors.RED}Invalid entry. Try again.{colors.RESET}")

print(f"{colors.CYAN}Welcome. You will be playing against an AI Poker Bot in heads up poker. You have chosen to buy in for {buyin}. The bot will match this stack, and the blinds are set at {buyin/100}/{buyin/50}.{colors.RESET}")

player1 = Player("Player", buyin)
player2 = AIPlayer("AI Bot", buyin)
player1.current_bet = 0
player2.current_bet = 0
hand_num = 0

dealer = player1

while player1.chips > 0 and player2.chips > 0:
    # Reset the pot and deal new cards
    hand_num = hand_num + 1
    pot = 0
    player1.folded = False
    player2.folded = False
    deck = Deck()
    player1.hand, player2.hand, deck = shuffle_deal(deck)
    community_cards = []

    # Determine who acts first based on the dealer
    if dealer == player1:
        first_actor, first_actor_bet, second_actor, second_actor_bet = player2, SMALL_BLIND, player1, BIG_BLIND
    else:
        first_actor, first_actor_bet, second_actor, second_actor_bet = player1, SMALL_BLIND, player2, BIG_BLIND

    # Display initial game state
    print(f"{colors.CYAN}Hand {hand_num}:\n{colors.RESET}{player1.name}{colors.CYAN}'s stack: {player1.chips}.\n{colors.RESET}{player2.name}{colors.CYAN}'s stack: {player2.chips}.{colors.RESET}")
    print(f"{first_actor.name}{colors.CYAN} is the Small Blind ({SMALL_BLIND}), {colors.RESET}{second_actor.name}{colors.CYAN} is the Big Blind ({BIG_BLIND}).\n{colors.RESET}{first_actor.name}{colors.CYAN} acts first.{colors.RESET}")
    first_actor.chips -= SMALL_BLIND
    second_actor.chips -= BIG_BLIND
    pot += SMALL_BLIND + BIG_BLIND
    display_game_state(player1, player2, pot, community_cards, False)
    
    # Run betting rounds and deal community cards
    pot = betting_round(first_actor, first_actor_bet, second_actor, second_actor_bet, pot, True)  # First betting round
    community_cards.extend(deck.deal(3))  # Deal the flop (3 cards)
    display_game_state(player1, player2, pot, community_cards, False)
    pot = betting_round(first_actor, 0, second_actor, 0, pot, False)  # Betting round after flop

    community_cards.extend(deck.deal(1))  # Deal the turn (1 card)
    display_game_state(player1, player2, pot, community_cards, False)
    pot = betting_round(first_actor, 0, second_actor, 0, pot, False)  # Betting round after turn

    community_cards.extend(deck.deal(1))  # Deal the river (1 card)
    display_game_state(player1, player2, pot, community_cards, False)
    pot = betting_round(first_actor, 0, second_actor, 0, pot, False)  # Final betting round

    # Display final game state
    display_game_state(player1, player2, pot, community_cards, True)

    # Determine and display the winner
    if player1.folded:
        player2.chips += pot
        print(f"{player2.name}{colors.CYAN} wins because {colors.RESET}{player1.name}{colors.CYAN} folded.{colors.RESET}")
    elif player2.folded:
        player1.chips += pot
        print(f"{player1.name}{colors.CYAN} wins because {colors.RESET}{player2.name}{colors.CYAN} folded.{colors.RESET}")
    else:
        winner = compare_hands(player1.hand, player2.hand, community_cards)
        if winner == player1:
            player1.chips += pot
        elif winner == player2:
            player2.chips += pot
        else:
            player1.chips += int(pot/2)
            player2.chips += int(pot/2)

    # Alternate the dealer for the next hand
    print(f"{player1.name}{colors.CYAN}'s stack: {player1.chips}.\n{colors.RESET}{player2.name}{colors.CYAN}'s stack: {player2.chips}.{colors.RESET}")
    dealer = player2 if dealer == player1 else player1

    # Check if the game should continue
    if player1.chips == 0 and player2.chips > 0:
        print(f"{colors.BLUE}Game over! {colors.RESET}{player2.name}{colors.BLUE} wins!{colors.RESET}")
        break
    elif player2.chips == 0 and player1.chips > 0:
        print(f"{colors.BLUE}Game over! {colors.RESET}{player1.name}{colors.BLUE} wins!{colors.RESET}")
        break

    continue_game = input(f"{colors.CYAN}Do you want to play another hand? (yes/no): {colors.RESET}").lower()
    if continue_game != 'yes':
        break