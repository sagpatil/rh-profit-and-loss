import requests
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn', to silence the errors about copy

### ORDER HISTORY STUFF ###

def get_symbol_from_instrument_url(url, df):

    try:
        symbol = df.loc[url]['symbol']
    
    except Exception as e:
        response = requests.get(url)
        symbol = response.json()['symbol']
        df.at[url, 'symbol'] = symbol
        # time.sleep(np.random.randint(low=0, high=2, size=(1))[0])
   
    return symbol, df

def order_item_info(order, df):
    #side: .side,  price: .average_price, shares: .cumulative_quantity, instrument: .instrument, date : .last_transaction_at
    symbol, df = get_symbol_from_instrument_url(order['instrument'], df)
    
    order_info_dict = {
        'side': order['side'],
        'avg_price': order['average_price'],
        'order_price': order['price'],
        'order_quantity': order['quantity'],
        'shares': order['cumulative_quantity'],
        'symbol': symbol,
        'id': order['id'],
        'date': order['last_transaction_at'],
        'state': order['state'],
        'type': order['type']
    }

    return order_info_dict


def mark_pending_orders(row):
    if row.state == 'queued' or row.state == 'confirmed':
        order_status_is_pending = True
    else:
        order_status_is_pending = False
    return order_status_is_pending
# df_order_history.apply(mark_pending_orders, axis=1)    


def get_order_history(my_trader):
    
    # Get unfiltered list of order history
    past_orders = my_trader.get_all_stock_orders()

    # Load in our pickled database of instrument-url lookups
    instruments_df = pd.read_pickle('symbol_and_instrument_urls')

    # Create a big dict of order history
    orders = [order_item_info(order, instruments_df) for order in past_orders]

    # Save our pickled database of instrument-url lookups
    instruments_df.to_pickle('symbol_and_instrument_urls')

    df = pd.DataFrame.from_records(orders)
    df['ticker'] = df['symbol']

    columns = ['ticker', 'state', 'order_quantity', 'shares', 'avg_price', 'date', 'id', 'order_price', 'side', 'symbol', 'type']
    df = df[columns]

    df['is_pending'] = df.apply(mark_pending_orders, axis=1)

    return df, instruments_df


def get_all_history_options_orders(r):

    options_orders = r.get_market_options()

    options_orders_cleaned = []
    
    for each in options_orders:
        if float(each['processed_premium']) < 1:
            continue
        else:
            if each['legs'][0]['position_effect'] == 'open':
                value = round(float(each['processed_premium']), 2)*-1
            else:
                value = round(float(each['processed_premium']), 2)
                
            one_order = [pd.to_datetime(each['created_at']), each['chain_symbol'], value, each['legs'][0]['position_effect']]
            options_orders_cleaned.append(one_order)
    
    df_options_orders_cleaned = pd.DataFrame(options_orders_cleaned)
    df_options_orders_cleaned.columns = ['date', 'ticker', 'value', 'position_effect']
    df_options_orders_cleaned = df_options_orders_cleaned.sort_values('date')
    df_options_orders_cleaned = df_options_orders_cleaned.set_index('date')

    return df_options_orders_cleaned


### END ORDER HISTORY GETTING STUFF ####