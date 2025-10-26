"""Main application - LangGraph workflow for trading analysis"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.graph import StateGraph, END
from models.state import TradingState
from agents.data_collector import collect_market_data
from agents.news_collector import collect_stock_news
from agents.btc_collector import collect_btc_data
from agents.ixic_collector import collect_ixic_data
from agents.analysis import analyze_market
from agents.decision_maker import make_decision
from agents.decision_minimal import make_decision_minimal
from agents.decision_macro import make_decision_macro
from agents.decision_intraday import make_decision_intraday
from agents.decision_intraday2 import make_decision_intraday2
from agents.paper_trading import execute_paper_trade
import config
import json
from datetime import datetime


def create_workflow() -> StateGraph:
    """
    Create LangGraph workflow with parallel 3-strategy execution
    
    Returns:
        Compiled StateGraph workflow
    """
    # Create graph
    workflow = StateGraph(TradingState)
    
    # Data collection nodes
    workflow.add_node("collect_data", collect_market_data)
    workflow.add_node("collect_news", collect_stock_news)
    workflow.add_node("collect_btc", collect_btc_data)
    workflow.add_node("collect_ixic", collect_ixic_data)
    
    # Analysis node
    workflow.add_node("analyze", analyze_market)
    
    # Decision nodes (5 strategies)
    workflow.add_node("decide_structured", make_decision)
    workflow.add_node("decide_minimal", make_decision_minimal)
    workflow.add_node("decide_macro", make_decision_macro)
    workflow.add_node("decide_intraday", make_decision_intraday)
    workflow.add_node("decide_intraday2", make_decision_intraday2)
    
    # Execution node
    workflow.add_node("execute_trade", execute_paper_trade)
    
    # Set entry point
    workflow.set_entry_point("collect_data")
    
    # Parallel data collection (3 collectors)
    workflow.add_edge("collect_data", "collect_news")
    workflow.add_edge("collect_data", "collect_btc")
    workflow.add_edge("collect_data", "collect_ixic")
    
    # All 3 data collectors must complete before analysis
    workflow.add_edge("collect_news", "analyze")
    workflow.add_edge("collect_btc", "analyze")
    workflow.add_edge("collect_ixic", "analyze")
    
    # PARALLEL EXECUTION: All 5 decision strategies run simultaneously
    workflow.add_edge("analyze", "decide_structured")
    workflow.add_edge("analyze", "decide_minimal")
    workflow.add_edge("analyze", "decide_macro")
    workflow.add_edge("analyze", "decide_intraday")
    workflow.add_edge("analyze", "decide_intraday2")
    
    # All 5 must complete before execution
    workflow.add_edge("decide_structured", "execute_trade")
    workflow.add_edge("decide_minimal", "execute_trade")
    workflow.add_edge("decide_macro", "execute_trade")
    workflow.add_edge("decide_intraday", "execute_trade")
    workflow.add_edge("decide_intraday2", "execute_trade")
    
    workflow.add_edge("execute_trade", END)
    
    # Compile
    return workflow.compile()


def print_final_result(state: TradingState):
    """Print final trading recommendation and execution (5 strategies)"""
    print("\n" + "="*70)
    print("📈 5-STRATEGY RECOMMENDATIONS & EXECUTION")
    print("="*70)
    
    if state.get('error'):
        print(f"\n❌ Error: {state['error']}")
        return
    
    rec_struct = state.get('recommendation_structured')
    rec_minimal = state.get('recommendation_minimal')
    rec_macro = state.get('recommendation_macro')
    rec_intraday = state.get('recommendation_intraday')
    rec_intraday2 = state.get('recommendation_intraday2')
    
    if not (rec_struct or rec_minimal or rec_macro or rec_intraday or rec_intraday2):
        print("\n❌ No recommendations available")
        return
    
    market_data = state.get('market_data')
    analysis = state.get('analysis')
    
    print(f"\n📊 Market: {state['symbol']}")
    print(f"💰 Current Price: ${market_data['current_price']}")
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show all 5 strategies
    print(f"\n🎯 STRATEGY RECOMMENDATIONS:")
    
    if rec_struct:
        print(f"\n📐 STRUCTURED: {rec_struct['action']} ({rec_struct.get('confidence', 'N/A')})")
        if rec_struct['action'] in ['LONG', 'SHORT'] and 'risk_management' in rec_struct:
            rm = rec_struct['risk_management']
            print(f"   Entry: ${rm['entry']} | SL: ${rm['stop_loss']} | TP: ${rm['take_profit']}")
    
    if rec_minimal:
        print(f"\n🤖 MINIMAL: {rec_minimal['action']} ({rec_minimal.get('confidence', 'N/A')})")
        if rec_minimal['action'] in ['LONG', 'SHORT'] and 'risk_management' in rec_minimal:
            rm = rec_minimal['risk_management']
            print(f"   Entry: ${rm['entry']} | SL: ${rm['stop_loss']} | TP: ${rm['take_profit']}")
    
    if rec_macro:
        print(f"\n🌍 MACRO: {rec_macro['action']} ({rec_macro.get('confidence', 'N/A')})")
        if rec_macro['action'] in ['LONG', 'SHORT'] and 'risk_management' in rec_macro:
            rm = rec_macro['risk_management']
            print(f"   Entry: ${rm['entry']} | SL: ${rm['stop_loss']} | TP: ${rm['take_profit']}")
        print(f"   (Considers: News sentiment + BTC + NASDAQ)")
    
    if rec_intraday:
        session = rec_intraday.get('session', 'N/A')
        print(f"\n⚡ INTRADAY: {rec_intraday['action']} ({rec_intraday.get('confidence', 'N/A')}) [{session}]")
        if rec_intraday['action'] in ['LONG', 'SHORT'] and 'risk_management' in rec_intraday:
            rm = rec_intraday['risk_management']
            print(f"   Entry: ${rm['entry']} | SL: ${rm['stop_loss']} (-{rm['stop_distance_percentage']}%) | TP: ${rm['take_profit']} (+{rm['tp_distance_percentage']}%)")
            print(f"   (Scalping: Session-aware, Tight stops)")
    
    if rec_intraday2:
        print(f"\n🔄 INTRADAY2: {rec_intraday2['action']} ({rec_intraday2.get('confidence', 'N/A')})")
        if rec_intraday2['action'] in ['LONG', 'SHORT'] and 'risk_management' in rec_intraday2:
            rm = rec_intraday2['risk_management']
            print(f"   Entry: ${rm['entry']} | TP1: ${rm['take_profit_1']} (+{rm['tp1_distance_pct']}%) | TP2: ${rm['take_profit_2']} (+{rm['tp2_distance_pct']}%)")
            print(f"   SL: ${rm['stop_loss']} (-{rm['stop_distance_pct']}%)")
            print(f"   (Mean Reversion: BB extremes, Quick scalps)")
    
    # Pick first non-None for detailed display
    recommendation = rec_struct or rec_minimal or rec_macro or rec_intraday or rec_intraday2
    
    # Risk Management (if LONG or SHORT)
    if 'risk_management' in recommendation:
        rm = recommendation['risk_management']
        print(f"\n💰 RISK MANAGEMENT (ATR-Driven):")
        print(f"   Entry Price:   ${rm['entry']}")
        print(f"   Stop Loss:     ${rm['stop_loss']} ({'-' if recommendation['action'] == 'LONG' else '+'}{rm['stop_distance_percentage']}%)")
        print(f"   Take Profit:   ${rm['take_profit']} ({'+' if recommendation['action'] == 'LONG' else '-'}{rm['tp_distance_percentage']}%)")
        print(f"   ")
        print(f"   Risk:   ${rm['risk_amount']} ({rm['stop_distance_percentage']}%)")
        print(f"   Reward: ${rm['reward_amount']} ({rm['tp_distance_percentage']}%)")
        print(f"   R/R Ratio: 1:{rm['risk_reward_ratio']}")
        print(f"   ")
        print(f"   ATR (14): ${rm['atr']} ({rm['atr_percentage']}% of price)")
        print(f"   Stop: {1.5}x ATR | Target: {3.0}x ATR")
    
    print(f"\n💡 Reasoning:")
    print(f"   {recommendation.get('reasoning', 'N/A')}")
    
    if 'key_factors' in recommendation:
        print(f"\n🔑 Key Factors:")
        for i, factor in enumerate(recommendation['key_factors'], 1):
            print(f"   {i}. {factor}")
    
    # Technical Summary
    if analysis:
        indicators = analysis['indicators']
        ind_higher = indicators['higher_tf']['indicators']
        ind_lower = indicators['lower_tf']['indicators']
        tf_higher = indicators['higher_tf']['timeframe']
        tf_lower = indicators['lower_tf']['timeframe']
        
        print(f"\n📊 Multi-Timeframe Technical Summary:")
        
        print(f"\n   📈 {tf_higher.upper()} (Trend):")
        print(f"      EMA: {ind_higher['ema']['trend']}")
        print(f"      MACD: {ind_higher['macd']['signal']}")
        print(f"      RSI: {ind_higher['rsi']['value']} ({ind_higher['rsi']['signal']})")
        
        print(f"\n   ⚡ {tf_lower.upper()} (Entry):")
        print(f"      EMA: {ind_lower['ema']['trend']}")
        print(f"      MACD: {ind_lower['macd']['signal']}")
        print(f"      RSI: {ind_lower['rsi']['value']} ({ind_lower['rsi']['signal']})")
        print(f"      BB: {ind_lower['bollinger_bands']['position']}")
        
        # Entry setup display
        entry_quality = analysis.get('entry_quality', 'unknown')
        confluence = analysis.get('confluence', 'unknown')
        reversal = analysis.get('reversal', {})
        
        print(f"\n   🎯 Entry Setup: {entry_quality.upper().replace('_', ' ')}")
        print(f"      Status: {confluence.replace('_', ' ')}")
        
        # Trend reversal detection (PRIORITY)
        if reversal.get('reversal_detected'):
            print(f"\n   🔄 TREND REVERSAL DETECTED!")
            print(f"      Type: {reversal['reversal_type'].replace('_', ' ').upper()}")
            print(f"      Strength: {reversal['strength_label'].upper()} ({reversal['strength']}/100)")
            print(f"      Confirmations: {reversal['confirmation_count']}")
            for factor in reversal['confirmation_factors']:
                print(f"         ✓ {factor}")
            
            if reversal['strength_label'] == 'strong':
                print(f"      💎 STRONG REVERSAL - Excellent early entry opportunity!")
            elif reversal['strength_label'] == 'medium':
                print(f"      ⚡ MEDIUM REVERSAL - Good opportunity if confirmed")
            else:
                print(f"      ⚠️  WEAK REVERSAL - Wait for more confirmation")
        
        # Quality indicator with context
        if entry_quality == "pullback_reversal":
            print(f"\n      💡 Pullback reversal - Usually better R/R")
            print(f"         (But check RSI, orderbook, MACD confirmation)")
        elif entry_quality == "trend_following":
            print(f"\n      📊 Trend running - Can work with strong confirmation")
            print(f"         (Need: Strong OB pressure + volume + RSI healthy)")
        elif entry_quality == "wait_for_reversal":
            print(f"\n      ⏳ In pullback - Wait for reversal signal")
        elif entry_quality == "avoid":
            print(f"\n      🚫 Unclear - Avoid trading")
        
        # Orderbook Summary
        orderbook = analysis['orderbook']
        print(f"\n📖 Orderbook:")
        print(f"   Bid/Ask: {orderbook['imbalance']['bid_percentage']:.1f}% / {orderbook['imbalance']['ask_percentage']:.1f}%")
        print(f"   Pressure: {orderbook['imbalance']['pressure']}")
        print(f"   Spread: {orderbook['spread']['percentage']:.4f}%")
        if orderbook['walls']['has_significant_walls']:
            print(f"   ⚠️  Large orders detected")
            if orderbook['walls']['bid_walls']:
                print(f"      Bid walls: {len(orderbook['walls']['bid_walls'])}")
            if orderbook['walls']['ask_walls']:
                print(f"      Ask walls: {len(orderbook['walls']['ask_walls'])}")
        
        sentiment = analysis['sentiment']
        print(f"\n💭 Sentiment:")
        print(f"   Funding: {sentiment['funding_sentiment']}")
        print(f"   Volume: {sentiment['volume_momentum']}")
        print(f"   Orderbook: {sentiment['orderbook_pressure']}")
    
    # Trade Execution Info
    if state.get('trade_execution'):
        trade_exec = state['trade_execution']
        if trade_exec.get('executed'):
            print(f"\n💼 PAPER TRADE EXECUTION:")
            print(f"   Status: ✅ EXECUTED")
            print(f"   Trade ID: {trade_exec['trade_id']}")
            print(f"   Stored in database: paper_trades.db")
            
            if 'stats' in trade_exec:
                stats = trade_exec['stats']
                print(f"\n   📊 Your Trading Stats:")
                print(f"      Total trades: {stats['total_trades']}")
                print(f"      Open: {stats['open_trades']} | Closed: {stats['closed_trades']}")
                if stats['closed_trades'] > 0:
                    print(f"      Win rate: {stats['win_rate']:.1f}%")
                    print(f"      Total P&L: ${stats['total_pnl']:.2f}")
        else:
            print(f"\n💼 PAPER TRADE EXECUTION:")
            print(f"   Status: ⏸️  NOT EXECUTED")
            print(f"   Reason: {trade_exec.get('reason', trade_exec.get('error', 'Unknown'))}")
    
    print("\n" + "="*60)


def main():
    """Main application entry point"""
    print("="*60)
    print("🚀 Multi-Agent Trading System")
    print("   Powered by LangGraph & DeepSeek AI")
    print("="*60)
    
    # Create workflow
    app = create_workflow()
    
    # Initialize state
    initial_state: TradingState = {
        "symbol": config.SYMBOL,
        "market_data": None,
        "news_data": None,
        "btc_data": None,
        "ixic_data": None,
        "analysis": None,
        "recommendation_structured": None,
        "recommendation_minimal": None,
        "recommendation_macro": None,
        "recommendation_intraday": None,
        "recommendation_intraday2": None,
        "trade_execution": None,
        "error": None
    }
    
    # Run workflow
    print(f"\n🔄 Starting analysis for {config.SYMBOL}...\n")
    
    try:
        result = app.invoke(initial_state)
        print_final_result(result)
        
        # Save result to file
        if result.get('recommendation'):
            # Create results directory if it doesn't exist
            results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results')
            os.makedirs(results_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(results_dir, f"result_{config.SYMBOL}_{timestamp}.json")
            
            # Prepare result for JSON (convert DataFrame to dict)
            save_result = {
                "symbol": result['symbol'],
                "timestamp": datetime.now().isoformat(),
                "current_price": result['market_data']['current_price'],
                "recommendation": result['recommendation'],
                "analysis_summary": result['analysis']['summary'],
                "indicators": result['analysis']['indicators'],
                "orderbook": result['analysis']['orderbook'],
                "sentiment": result['analysis']['sentiment']
            }
            
            # Convert numpy types to native Python types
            def convert_types(obj):
                import numpy as np
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_types(item) for item in obj]
                return obj
            
            save_result = convert_types(save_result)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_result, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Result saved to: {os.path.basename(filename)}")
            print(f"   Location: {filename}")
        
    except Exception as e:
        print(f"\n❌ Error running workflow: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

