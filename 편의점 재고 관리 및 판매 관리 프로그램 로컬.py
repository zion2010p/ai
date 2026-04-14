import datetime
import urllib.parse
import webbrowser

# ==========================================
# 📊 전역 데이터
# ==========================================
total_revenue = 0
total_waste_loss = 0
global_waste_list = []

# ==========================================
# 🖼️ [자동화] 이미지 브라우저 팝업 함수
# ==========================================
def auto_display_image(item_name):
    """상품명만 받아서 기본 웹 브라우저로 사진 검색 결과를 자동으로 띄워주는 함수"""
    print(f"  📸 [{item_name}] 사진을 웹 브라우저에서 띄웁니다...")
    search_keyword = urllib.parse.quote(item_name + " 편의점")
    search_url = f"https://www.google.com/search?q={search_keyword}&tbm=isch"
    
    # 기본 웹 브라우저의 새 탭에서 URL 열기
    webbrowser.open(search_url)

# ==========================================
# 🛠️ 핵심 기능 함수
# ==========================================

def setup_inventory(inventory):
    """1. 상품 입고 (등록 즉시 자동 사진 출력)"""
    print("\n=== [📦 신규 상품 입고] ===")
    print("'그만'을 입력하면 마칩니다.\n")

    while True:
        name = input("📍 상품명 (또는 '그만'): ").strip()
        if name in ['그만', 'exit', 'quit', '']:
            break

        try:
            if name not in inventory:
                price = int(input(f"  💰 '{name}'의 가격(원): "))
                category = input(f"  📁 '{name}'의 카테고리: ").strip()
                inventory[name] = {"price": price, "category": category, "sold": 0, "batches": []}
            else:
                print(f"  ℹ️ 이미 등록된 상품입니다. 추가 입고합니다.")

            stock = int(input(f"  🔢 입고 수량(개): "))
            exp_date_str = input(f"  📅 유통기한 (예: 2026-04-20): ").strip()
            exp_date = datetime.datetime.strptime(exp_date_str, "%Y-%m-%d").date()

            inventory[name]["batches"].append({"stock": stock, "exp_date": exp_date})
            inventory[name]["batches"].sort(key=lambda x: x["exp_date"])

            print(f"  ✅ '{name}' 입고 완료!\n")

            # 🔥 자동 이미지 팝업 실행
            auto_display_image(name)

        except ValueError:
            print("  ⚠️ 날짜(YYYY-MM-DD) 또는 숫자 형식이 잘못되었습니다.\n")

    return inventory

def process_cart(inventory):
    """2. 장바구니 결제 (선입선출)"""
    global total_revenue
    cart = {}
    today = datetime.date.today()

    print("\n=== [🛒 장바구니 결제] ===")
    while True:
        item_name = input("구매할 상품명 (결제/취소): ").strip()
        if item_name == '결제': break
        if item_name == '취소': return

        if item_name not in inventory:
            print("  ❌ 등록되지 않은 상품입니다.")
            continue

        product = inventory[item_name]
        sellable_stock = sum(b['stock'] for b in product['batches'] if b['exp_date'] >= today)

        if sellable_stock == 0:
            print(f"  ❌ 실패: 정상 재고가 없습니다.")
            continue

        try:
            quantity = int(input(f"'{item_name}' 구매 수량 (최대 {sellable_stock}개): "))
            if quantity > sellable_stock:
                print(f"  ❌ 수량 초과입니다.")
                continue
            cart[item_name] = cart.get(item_name, 0) + quantity
        except ValueError:
            print("  ❌ 숫자로 입력해주세요.")

    if not cart: return

    print("\n[💳 결제 진행 (선입선출)]")
    cart_total = 0

    for item_name, quantity in cart.items():
        product = inventory[item_name]
        remaining = quantity

        for batch in product["batches"]:
            if batch["exp_date"] < today: continue
            if remaining == 0: break

            if batch["stock"] <= remaining:
                remaining -= batch["stock"]
                batch["stock"] = 0
            else:
                batch["stock"] -= remaining
                remaining = 0

        product["batches"] = [b for b in product["batches"] if b["stock"] > 0]
        product["sold"] += quantity
        price = product["price"] * quantity
        cart_total += price
        total_revenue += price
        print(f"  ✅ {item_name} 총 {quantity}개: {price}원 완료")

    print(f"\n💰 이번 결제 총 금액: {cart_total}원")

def check_inventory(inventory):
    """3. 재고 현황 조회 (조회 시 상품 이미지 자동 출력 여부 확인)"""
    print("\n=== [📦 전체 재고 및 유통기한 현황] ===")
    today = datetime.date.today()
    if not inventory:
        print("  등록된 상품이 없습니다.")
        return

    for name, info in inventory.items():
        total_stock = sum(b['stock'] for b in info['batches'])
        print(f"\n▶ {name} (가격: {info['price']}원 | 총 재고: {total_stock}개 | 판매: {info['sold']}개)")

        for batch in info["batches"]:
            days_left = (batch["exp_date"] - today).days
            status = "🚨 폐기 대상" if days_left < 0 else "⚠️ 임박" if days_left <= 3 else "✅ 정상"
            print(f"   - 기한: {batch['exp_date']} | 재고: {batch['stock']}개 | {status}")
            
        # 재고 조회 시 한 번에 인터넷 창이 너무 많이 열리는 것을 방지하기 위한 선택지
        show_img = input(f"   💡 '{name}'의 사진을 확인하시겠습니까? (y/n): ").strip().lower()
        if show_img == 'y':
            auto_display_image(name)

def identify_and_manage_waste(inventory):
    """4. 폐기 처리"""
    global global_waste_list, total_waste_loss
    today = datetime.date.today()

    for item_name, info in inventory.items():
        expired = [b for b in info['batches'] if b['exp_date'] < today]
        valid = [b for b in info['batches'] if b['exp_date'] >= today]
        if expired:
            for batch in expired:
                global_waste_list.append({"name": item_name, "quantity": batch['stock'], "exp_date": batch['exp_date'], "loss": batch['stock'] * info['price']})
            info['batches'] = valid

    while True:
        print(f"\n=== [🗑️ 폐기 관리 (대기 {len(global_waste_list)}건)] ===")
        if not global_waste_list:
            print("  ✅ 대기 중인 폐기 물품이 없습니다.")
            break
        for i, item in enumerate(global_waste_list):
            print(f"  [{i}] {item['name']} | {item['quantity']}개 | 손실: {item['loss']}원")

        choice = input("선택 (번호/all/exit): ").strip()
        if choice == 'exit': break
        elif choice == 'all':
            total_waste_loss += sum(item['loss'] for item in global_waste_list)
            global_waste_list.clear()
            print("  ✅ 전체 처리 완료")
            break
        elif choice.isdigit() and int(choice) < len(global_waste_list):
            removed = global_waste_list.pop(int(choice))
            total_waste_loss += removed['loss']
            print(f"  ✅ '{removed['name']}' 처리 완료")

def show_closing_stats(inventory):
    """5. 영업 마감"""
    print("\n=== [🌙 영업 마감] ===")
    print(f"  💵 일일 총 매출: {total_revenue}원")
    print(f"  💸 일일 폐기 손실액: {total_waste_loss}원")
    print(f"  📊 예상 순이익: {total_revenue - total_waste_loss}원")
    print("시스템을 종료합니다.")

# ==========================================
# 🚀 메인 프로그램 루프
# ==========================================
if __name__ == "__main__":
    my_inventory = {}
    print("🏪 스마트 편의점 관리 시스템 시작 (자동 웹 이미지 기능 포함)")

    while True:
        print("\n" + "="*45)
        print("1. [📦 입고] 신규 상품 추가 (자동 사진 띄움)")
        print("2. [🛒 판매] 장바구니 결제 (선입선출)")
        print("3. [📋 조회] 전체 재고 확인")
        print("4. [🗑️ 폐기] 폐기 물품 처리")
        print("5. [🌙 마감] 통계 확인 및 종료")
        print("="*45)

        menu = input("원하는 작업 번호: ").strip()

        if menu == '1':
            my_inventory = setup_inventory(my_inventory)
        elif menu == '2':
            process_cart(my_inventory)
        elif menu == '3':
            check_inventory(my_inventory)
        elif menu == '4':
            identify_and_manage_waste(my_inventory)
        elif menu == '5':
            show_closing_stats(my_inventory)
            break
        else:
            print("❌ 올바른 메뉴 번호를 입력하세요.")
