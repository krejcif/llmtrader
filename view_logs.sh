#!/bin/bash
# Log Viewer Helper Script

LOG_DIR="logs"

show_menu() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 BOT LOG VIEWER"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1) Live main log (tail -f)"
    echo "2) Live errors only"
    echo "3) Show recent analyses"
    echo "4) Show trade closures"
    echo "5) Show winning trades"
    echo "6) Show losing trades"
    echo "7) Show TP hits"
    echo "8) Show SL hits"
    echo "9) Count statistics"
    echo "0) Exit"
    echo ""
}

if [ ! -d "$LOG_DIR" ]; then
    echo "❌ Logs directory not found. Run bot first to create logs."
    exit 1
fi

if [ "$1" ]; then
    # Direct command mode
    case $1 in
        live|tail)
            tail -f $LOG_DIR/trading_bot.log
            ;;
        errors)
            tail -f $LOG_DIR/bot_errors.log
            ;;
        analyses)
            grep "ANALYSIS.*STARTED" $LOG_DIR/trading_bot.log | tail -20
            ;;
        closures)
            grep "TRADE CLOSED:" $LOG_DIR/trading_bot.log | tail -20
            ;;
        wins)
            grep "TRADE CLOSED" $LOG_DIR/trading_bot.log | grep "P&L: +" | tail -20
            ;;
        losses)
            grep "TRADE CLOSED" $LOG_DIR/trading_bot.log | grep "P&L: -" | tail -20
            ;;
        stats)
            echo "📊 Log Statistics:"
            echo "  Analyses: $(grep -c "ANALYSIS.*STARTED" $LOG_DIR/trading_bot.log 2>/dev/null || echo 0)"
            echo "  Trades created: $(grep -c "Paper trade created" $LOG_DIR/trading_bot.log 2>/dev/null || echo 0)"
            echo "  Trades closed: $(grep -c "TRADE CLOSED:" $LOG_DIR/trading_bot.log 2>/dev/null || echo 0)"
            echo "  TP hits: $(grep -c "TP_HIT" $LOG_DIR/trading_bot.log 2>/dev/null || echo 0)"
            echo "  SL hits: $(grep -c "SL_HIT" $LOG_DIR/trading_bot.log 2>/dev/null || echo 0)"
            echo "  Errors: $(wc -l < $LOG_DIR/bot_errors.log 2>/dev/null || echo 0)"
            ;;
        *)
            echo "Usage: $0 [live|errors|analyses|closures|wins|losses|stats]"
            exit 1
            ;;
    esac
else
    # Interactive menu
    while true; do
        show_menu
        read -p "Select option: " choice
        
        case $choice in
            1)
                echo "📊 Live main log (Ctrl+C to exit)..."
                tail -f $LOG_DIR/trading_bot.log
                ;;
            2)
                echo "❌ Live errors (Ctrl+C to exit)..."
                tail -f $LOG_DIR/bot_errors.log
                ;;
            3)
                echo "📊 Recent Analyses:"
                grep "ANALYSIS.*STARTED" $LOG_DIR/trading_bot.log | tail -20
                read -p "Press Enter to continue..."
                ;;
            4)
                echo "💼 Trade Closures:"
                grep "TRADE CLOSED:" $LOG_DIR/trading_bot.log | tail -20
                read -p "Press Enter to continue..."
                ;;
            5)
                echo "✅ Winning Trades:"
                grep "TRADE CLOSED" $LOG_DIR/trading_bot.log | grep "P&L: +" | tail -20
                read -p "Press Enter to continue..."
                ;;
            6)
                echo "❌ Losing Trades:"
                grep "TRADE CLOSED" $LOG_DIR/trading_bot.log | grep "P&L: -" | tail -20
                read -p "Press Enter to continue..."
                ;;
            7)
                echo "🎯 Take Profit Hits:"
                grep "TP_HIT" $LOG_DIR/trading_bot.log | tail -20
                read -p "Press Enter to continue..."
                ;;
            8)
                echo "🛑 Stop Loss Hits:"
                grep "SL_HIT" $LOG_DIR/trading_bot.log | tail -20
                read -p "Press Enter to continue..."
                ;;
            9)
                echo ""
                echo "📊 Log Statistics:"
                echo "  Analyses: $(grep -c "ANALYSIS.*STARTED" $LOG_DIR/trading_bot.log 2>/dev/null || echo 0)"
                echo "  Trades created: $(grep -c "Paper trade created" $LOG_DIR/trading_bot.log 2>/dev/null || echo 0)"
                echo "  Trades closed: $(grep -c "TRADE CLOSED:" $LOG_DIR/trading_bot.log 2>/dev/null || echo 0)"
                echo "  TP hits: $(grep -c "TP_HIT" $LOG_DIR/trading_bot.log 2>/dev/null || echo 0)"
                echo "  SL hits: $(grep -c "SL_HIT" $LOG_DIR/trading_bot.log 2>/dev/null || echo 0)"
                echo "  Errors: $(wc -l < $LOG_DIR/bot_errors.log 2>/dev/null || echo 0)"
                echo ""
                read -p "Press Enter to continue..."
                ;;
            0)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo "Invalid option"
                ;;
        esac
    done
fi

