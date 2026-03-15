#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SKILLS_DIR=".claude/skills"
ISSUES=0
PASSED=0

echo "Validating GrowthLint Skills"
echo "============================"
echo ""

if [ ! -d "$SKILLS_DIR" ]; then
    echo -e "${RED}ERROR: Skills directory not found at $SKILLS_DIR${NC}"
    exit 1
fi

for skill_dir in "$SKILLS_DIR"/*/; do
    skill_name=$(basename "$skill_dir")
    skill_file="$skill_dir/SKILL.md"

    if [ ! -f "$skill_file" ]; then
        echo -e "${RED}FAIL${NC} $skill_name - Missing SKILL.md"
        ISSUES=$((ISSUES + 1))
        continue
    fi

    # Check file is not empty
    if [ ! -s "$skill_file" ]; then
        echo -e "${RED}FAIL${NC} $skill_name - SKILL.md is empty"
        ISSUES=$((ISSUES + 1))
        continue
    fi

    # Check for required sections
    has_description=false
    has_instructions=false

    if grep -qi "description\|when to use\|trigger" "$skill_file"; then
        has_description=true
    fi

    if grep -qi "instructions\|steps\|workflow\|procedure" "$skill_file"; then
        has_instructions=true
    fi

    if [ "$has_description" = true ] && [ "$has_instructions" = true ]; then
        echo -e "${GREEN}PASS${NC} $skill_name"
        PASSED=$((PASSED + 1))
    else
        if [ "$has_description" = false ]; then
            echo -e "${YELLOW}WARN${NC} $skill_name - No description/trigger section found"
        fi
        if [ "$has_instructions" = false ]; then
            echo -e "${YELLOW}WARN${NC} $skill_name - No instructions section found"
        fi
        PASSED=$((PASSED + 1))
    fi
done

echo ""
echo "============================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$ISSUES${NC}"
echo ""

if [ $ISSUES -gt 0 ]; then
    exit 1
fi

echo -e "${GREEN}All skills validated.${NC}"
