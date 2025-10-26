"""Generic Decision Wrapper - Adapts decision functions to work with strategy configs"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import TradingState


def make_decision_generic(state: TradingState, strategy_name: str, decision_func) -> TradingState:
    """
    Generic wrapper for decision functions
    
    Maps generic state keys to expected keys for decision functions
    
    Args:
        state: Current trading state
        strategy_name: Strategy name
        decision_func: Actual decision function to call
        
    Returns:
        Updated state with recommendation
    """
    market_data_key = f"market_data_{strategy_name}"
    analysis_key = f"analysis_{strategy_name}"
    recommendation_key = f"recommendation_{strategy_name}"
    
    # Check if we have required data
    if not state.get(analysis_key):
        print(f"❌ [{strategy_name.upper()}] No analysis data available")
        state[recommendation_key] = None
        return state
    
    # Create temporary state with expected keys for the decision function
    temp_state = {
        'symbol': state['symbol'],
        'market_data': state.get(market_data_key),
        'analysis': state.get(analysis_key),
        'error': state.get('error'),
        # Copy other shared data (news, btc, ixic) if strategy needs it
        'news_data': state.get('news_data'),
        'btc_data': state.get('btc_data'),
        'ixic_data': state.get('ixic_data'),
    }
    
    # Call the actual decision function
    result = decision_func(temp_state)
    
    # DEBUG: Show what decision function returned
    print(f"   [DEBUG GENERIC] Decision function returned: {list(result.keys()) if isinstance(result, dict) else type(result)}")
    if isinstance(result, dict) and recommendation_key.replace('recommendation_', '') in ['minimal', 'minimalbtc', 'macro']:
        rec_val = result.get(recommendation_key) or result.get('recommendation')
        if rec_val:
            print(f"   [DEBUG GENERIC] Found recommendation: action={rec_val.get('action')}")
    
    # Extract recommendation from result
    # Decision functions return either full state or partial update
    if isinstance(result, dict):
        # Check for strategy-specific recommendation key first
        if recommendation_key in result:
            state[recommendation_key] = result[recommendation_key]
            print(f"   [DEBUG GENERIC] ✅ Set {recommendation_key} from direct key")
        # Otherwise look for generic patterns
        elif 'recommendation' in result:
            state[recommendation_key] = result['recommendation']
            print(f"   [DEBUG GENERIC] ✅ Set {recommendation_key} from 'recommendation' key")
        # Or strategy-suffixed keys (e.g., recommendation_minimal)
        else:
            for key, value in result.items():
                if key.startswith('recommendation_'):
                    state[recommendation_key] = value
                    print(f"   [DEBUG GENERIC] ✅ Set {recommendation_key} from {key}")
                    break
            else:
                # No recommendation found
                state[recommendation_key] = None
                print(f"   [DEBUG GENERIC] ❌ No recommendation found in result")
    else:
        state[recommendation_key] = None
        print(f"   [DEBUG GENERIC] ❌ Result is not dict")
    
    return state

