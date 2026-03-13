#!/bin/bash
# Job Board Crawler - Linux/macOS execution script (moved to scripts/)
# Usage: ./scripts/run_crawler.sh [mode] [options]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$REPO_ROOT/.venv"
OUTPUT_DIR="$REPO_ROOT/output"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
print_banner() {
    echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     Job Board Discovery Crawler v1.0       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
}

# Print usage
print_usage() {
    echo -e "${YELLOW}Usage: ./scripts/run_crawler.sh [MODE] [OPTIONS]${NC}"
    echo ""
    echo "MODES:"
    echo "  quick       - Discover 10 job boards (default)"
    echo "  standard    - Discover 50 job boards"
    echo "  extensive   - Discover 100+ job boards with career pages"
    echo "  resume      - Resume from last checkpoint"
    echo "  test        - Run unit tests only"
    echo ""
    echo "OPTIONS:"
    echo "  --help      - Show this message"
    echo "  --engine    - Specify search engine (brave/duckduckgo)"
    echo "  --limit N   - Override limit (e.g., --limit 25)"
    echo ""
    echo "EXAMPLES:"
    echo "  ./scripts/run_crawler.sh quick"
    echo "  ./scripts/run_crawler.sh standard --engine brave"
    echo "  ./scripts/run_crawler.sh extensive --limit 75"
    echo "  ./scripts/run_crawler.sh resume"
}

# Check virtual environment
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        echo -e "${RED}✗ Virtual environment not found at $VENV_PATH${NC}"
        echo -e "${YELLOW}Please run: python3 -m venv $VENV_PATH${NC}"
        exit 1
    fi
}

# Activate virtual environment
activate_venv() {
    if [ -f "$VENV_PATH/bin/activate" ]; then
        # shellcheck source=/dev/null
        source "$VENV_PATH/bin/activate"
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
    else
        echo -e "${RED}✗ Failed to activate virtual environment${NC}"
        exit 1
    fi
}

# Create output directory
create_output_dir() {
    mkdir -p "$OUTPUT_DIR"
    echo -e "${GREEN}✓ Output directory ready: $OUTPUT_DIR${NC}"
}

# Run the crawler with specified mode
run_crawler() {
    local mode=$1
    shift
    local extra_args="$@"
    
    local limit=10
    local detect_careers=""
    local output_name="job_discovery"
    
    case "$mode" in
        quick)
            limit=10
            output_name="quick_discovery"
            ;;
        standard)
            limit=50
            output_name="standard_discovery"
            ;;
        extensive)
            limit=100
            detect_careers="--detect-careers"
            output_name="extensive_discovery"
            ;;
        resume)
            echo -e "${BLUE}🔄 Resuming from last checkpoint...${NC}"
            python3 "$REPO_ROOT/run.py" --engine brave --filter --resume $extra_args
            return $?
            ;;
        test)
            echo -e "${BLUE}🧪 Running unit tests...${NC}"
            python3 << 'TESTEOF'
from crawler import DuckDuckGoJobBoardCrawler
print("\n" + "="*60)
print("UNIT TESTS")
print("="*60)
c = DuckDuckGoJobBoardCrawler()
tests_passed = 0
tests_total = 0

# Aggregator detection
tests = [("https://indeed.com", True), ("https://linkedin.com", True), ("https://acme.com", False)]
for url, expected in tests:
    result = c.is_job_aggregator(url)
    tests_total += 1
    if result == expected:
        tests_passed += 1
        print(f"✓ Aggregator detection: {url}")
    else:
        print(f"✗ Aggregator detection: {url} (expected {expected}, got {result})")

# Job heuristics
heur_tests = [("https://acme-careers.com", True), ("https://jobs.acme.com", True), ("https://acme.com", False)]
for url, expected in heur_tests:
    result = c.is_likely_job_board(url)
    tests_total += 1
    if result == expected:
        tests_passed += 1
        print(f"✓ Job board heuristic: {url}")
    else:
        print(f"✗ Job board heuristic: {url}")

print("\n" + "="*60)
print(f"Tests: {tests_passed}/{tests_total} passed")
print("="*60)
TESTEOF
            return 0
            ;;
        *)
            echo -e "${RED}✗ Unknown mode: $mode${NC}"
            print_usage
            exit 1
            ;;
    esac
    
    echo -e "${BLUE}🕷️  Crawling job boards (limit: $limit)...${NC}"
    python3 "$REPO_ROOT/run.py" --engine brave --filter --limit $limit $detect_careers --output "$REPO_ROOT/output/$output_name" $extra_args
}

# Main execution
main() {
    print_banner
    
    if [ "$#" -eq 0 ] || [ "$1" = "--help" ]; then
        print_usage
        exit 0
    fi
    
    check_venv
    activate_venv
    create_output_dir
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local mode=${1:-quick}
    shift || true
    
    if run_crawler "$mode" "$@"; then
        echo ""
        echo -e "${GREEN}✓ Crawler completed successfully!${NC}"
        echo -e "${BLUE}📂 Results saved to: $OUTPUT_DIR${NC}"
        echo ""
        ls -lh "$OUTPUT_DIR"/*.xlsx 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
        echo ""
    else
        echo ""
        echo -e "${RED}✗ Crawler encountered an error${NC}"
        exit 1
    fi
}

main "$@"
