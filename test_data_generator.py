"""
Test Data Generator for BaseballBinder Dashboard

This script populates the database with realistic test data for dashboard development.
Run this before implementing dashboard features to have data to work with.

Usage:
    python test_data_generator.py

Options:
    --cards N       Number of cards to generate (default: 200)
    --clear         Clear existing data before generating
    --skip-history  Skip generating price history data

Example:
    python test_data_generator.py --cards 500 --clear
"""

import random
import argparse
from datetime import datetime, timedelta, timezone
from models import Base, Card, CardPriceHistory, engine, get_db
from sqlalchemy.orm import Session

# Sample data pools
PLAYERS = [
    "Derek Jeter", "Mike Trout", "Shohei Ohtani", "Aaron Judge", "Mookie Betts",
    "Ronald Acuña Jr.", "Juan Soto", "Vladimir Guerrero Jr.", "Fernando Tatis Jr.",
    "Bryce Harper", "Freddie Freeman", "Yordan Alvarez", "Jose Altuve", "Corey Seager",
    "Kyle Tucker", "Rafael Devers", "Pete Alonso", "Bo Bichette", "Julio Rodriguez",
    "Spencer Strider", "Gerrit Cole", "Sandy Alcantara", "Shane McClanahan", "Corbin Burnes"
]

TEAMS = [
    "Yankees", "Red Sox", "Dodgers", "Angels", "Astros", "Braves", "Mets",
    "Phillies", "Padres", "Blue Jays", "Guardians", "Mariners", "Rangers",
    "Cardinals", "Cubs", "Giants", "Diamondbacks", "Rays", "Orioles", "Twins"
]

SETS = [
    "Topps", "Topps Chrome", "Bowman", "Bowman Chrome", "Topps Series 1",
    "Topps Series 2", "Topps Update", "Topps Heritage", "Topps Allen & Ginter",
    "Bowman Draft", "Topps Finest", "Topps Stadium Club", "Donruss", "Panini Prizm",
    "Select", "Topps Fire", "Topps Gallery", "Topps Big League"
]

YEARS = ["2020", "2021", "2022", "2023", "2024"]

PARALLELS = [
    None, None, None,  # 60% base cards
    "Refractor", "Blue", "Red", "Gold", "Green", "Orange", "Purple",
    "Black", "Silver", "Pink", "Camo", "Sepia", "Negative"
]

VARIETIES = [
    None, None, None, None,  # 80% no variety
    "Rookie Card", "All-Star", "Home Run Derby", "World Series",
    "Championship", "Award Winner", "Record Breaker"
]

def generate_card_number():
    """Generate a realistic card number"""
    return str(random.randint(1, 330))

def generate_numbered():
    """Generate numbered card designation (e.g., '05/49')"""
    if random.random() < 0.15:  # 15% are numbered
        serial = random.randint(1, 99)
        total = random.choice([25, 49, 50, 75, 99, 100, 150, 199, 250, 499])
        return f"{serial:02d}/{total}"
    return None

def generate_price():
    """Generate realistic price based on card type"""
    # Most cards are $1-10
    if random.random() < 0.6:
        return round(random.uniform(1, 10), 2)
    # Some are $10-50
    elif random.random() < 0.85:
        return round(random.uniform(10, 50), 2)
    # Few are $50-200
    elif random.random() < 0.95:
        return round(random.uniform(50, 200), 2)
    # Very few are $200-1000
    else:
        return round(random.uniform(200, 1000), 2)

def generate_cards(session: Session, num_cards: int):
    """Generate random cards"""
    print(f"Generating {num_cards} cards...")

    cards = []
    for i in range(num_cards):
        player = random.choice(PLAYERS)
        set_name = random.choice(SETS)
        year = random.choice(YEARS)
        team = random.choice(TEAMS)
        parallel = random.choice(PARALLELS)
        variety = random.choice(VARIETIES)
        numbered = generate_numbered()
        autograph = random.random() < 0.08  # 8% autographs
        graded = random.choice([None, None, None, "PSA 9", "PSA 10", "BGS 9.5"]) if random.random() < 0.1 else None

        price_paid = generate_price()
        current_value = price_paid * random.uniform(0.5, 3.0)  # Value can go up or down

        # Some cards are tracked
        tracked = random.random() < 0.15 if i < 20 else False  # First 20 cards have higher chance

        # Random creation date in last 6 months
        days_ago = random.randint(0, 180)
        created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)

        card = Card(
            set_name=set_name,
            card_number=generate_card_number(),
            player=player,
            team=team,
            year=year,
            variety=variety,
            parallel=parallel,
            autograph=autograph,
            numbered=numbered,
            graded=graded,
            price_paid=price_paid,
            current_value=round(current_value, 2),
            quantity=random.choice([1, 1, 1, 2, 3]),  # Most cards have qty 1
            tracked_for_pricing=tracked,
            last_price_check=created_at if tracked else None,
            ebay_avg_price=round(current_value, 2) if tracked else None,
            created_at=created_at,
            updated_at=created_at,
        )

        # Add preview image URL for tracked cards
        if tracked and random.random() < 0.7:  # 70% of tracked cards have images
            card.preview_image_url = f"https://i.ebayimg.com/images/g/sample{i}/s-l800.jpg"
            card.preview_fit = random.choice(['cover', 'contain'])
            card.preview_focus = random.uniform(30, 70)
            card.preview_zoom = random.uniform(0.8, 1.5)

        cards.append(card)

        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/{num_cards} cards...")

    session.bulk_save_objects(cards)
    session.commit()
    print(f"✅ Generated {num_cards} cards")

    return cards

def generate_price_history(session: Session, cards: list, skip: bool = False):
    """Generate price history for tracked cards"""
    if skip:
        print("⏭️  Skipping price history generation")
        return

    tracked_cards = [c for c in cards if c.tracked_for_pricing]

    if not tracked_cards:
        print("⚠️  No tracked cards found, skipping price history")
        return

    print(f"Generating price history for {len(tracked_cards)} tracked cards...")

    histories = []
    for card in tracked_cards:
        # Generate 10-30 historical price points
        num_points = random.randint(10, 30)
        base_price = card.current_value

        for i in range(num_points):
            days_ago = random.randint(1, 90)
            timestamp = datetime.now(timezone.utc) - timedelta(days=days_ago)

            # Price fluctuates around base price
            fluctuation = random.uniform(0.7, 1.3)
            price = base_price * fluctuation

            history = CardPriceHistory(
                card_id=card.id,
                price=round(price, 2),
                source='ebay_browse',
                timestamp=timestamp
            )
            histories.append(history)

    session.bulk_save_objects(histories)
    session.commit()
    print(f"✅ Generated {len(histories)} price history entries")

def clear_existing_data(session: Session):
    """Clear all existing cards and price history"""
    print("🗑️  Clearing existing data...")
    session.query(CardPriceHistory).delete()
    session.query(Card).delete()
    session.commit()
    print("✅ Existing data cleared")

def print_summary(session: Session):
    """Print summary statistics"""
    total_cards = session.query(Card).count()
    tracked_cards = session.query(Card).filter(Card.tracked_for_pricing == True).count()
    autographs = session.query(Card).filter(Card.autograph == True).count()
    numbered = session.query(Card).filter(Card.numbered.isnot(None)).count()
    graded = session.query(Card).filter(Card.graded.isnot(None)).count()
    history_entries = session.query(CardPriceHistory).count()

    total_value = session.query(Card.current_value).all()
    total_value = sum([v[0] for v in total_value if v[0]])

    print("\n" + "="*50)
    print("📊 DATABASE SUMMARY")
    print("="*50)
    print(f"Total Cards:          {total_cards}")
    print(f"Tracked Cards:        {tracked_cards}")
    print(f"Autographs:           {autographs}")
    print(f"Numbered Cards:       {numbered}")
    print(f"Graded Cards:         {graded}")
    print(f"Price History Points: {history_entries}")
    print(f"Total Collection Value: ${total_value:,.2f}")
    print("="*50)
    print("\n✅ Test data generation complete!")
    print("\nYou can now:")
    print("  1. Start the backend: python -m uvicorn main:app --reload")
    print("  2. Test endpoints: http://127.0.0.1:8000/stats/")
    print("  3. Start frontend: cd frontend && npm start")
    print("\n")

def main():
    parser = argparse.ArgumentParser(description='Generate test data for BaseballBinder dashboard')
    parser.add_argument('--cards', type=int, default=200, help='Number of cards to generate (default: 200)')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before generating')
    parser.add_argument('--skip-history', action='store_true', help='Skip generating price history data')

    args = parser.parse_args()

    print("\n" + "="*50)
    print("🎲 BASEBALLBINDER TEST DATA GENERATOR")
    print("="*50 + "\n")

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    # Get database session
    db = next(get_db())

    try:
        if args.clear:
            clear_existing_data(db)

        cards = generate_cards(db, args.cards)
        generate_price_history(db, cards, args.skip_history)
        print_summary(db)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
