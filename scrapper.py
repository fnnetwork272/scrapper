import re  
import asyncio  
from telethon import TelegramClient, events  

# API Configuration  
api_id = 25031007  # Replace with your actual API ID
api_hash = "68029e5e2d9c4dd11f600e1692c3acaa"  # Replace with your actual API hash
session_name = "cc_scraper"  

# Sources Configuration - add as many as needed
source_groups = [-1002410570317]  # Add source group IDs if needed
source_channels = []  # Add source channel IDs if needed

# Target channels where scraped CCs will be sent (you can add multiple IDs)
target_channels = [-1002319403142]  # Add more channel IDs as needed
# For example: target_channels = [-1002380708969, -1001234567890]

# Initialize client
client = TelegramClient(session_name, api_id, api_hash)  

# Enhanced CC patterns to capture more formats
cc_patterns = [
    # Standard formats with different separators
    r'(\d{13,16})[\s|/|\-|~]?\s*(\d{1,2})[\s|/|\-|~]?\s*(\d{2,4})[\s|/|\-|~]?\s*(\d{3,4})',
    r'(\d{13,16})\s(\d{1,2})\s(\d{2,4})\s(\d{3,4})',
    
    # Newline separated formats
    r'(\d{13,16})\n(\d{1,2})\n(\d{2,4})\n(\d{3,4})',
    r'(\d{13,16})\n(\d{1,2})[/|-](\d{2,4})\n(\d{3,4})',
    
    # Additional formats often found in groups
    r'(\d{13,16})[:|=|>]?(\d{1,2})[:|=|>]?(\d{2,4})[:|=|>]?(\d{3,4})',
    r'(\d{13,16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})',
    
    # Format with labels
    r'cc(?:num)?:[\s]?(\d{13,16})[\s\n]+(?:exp|expiry|expiration):[\s]?(\d{1,2})[/|-](\d{2,4})[\s\n]+(?:cvv|cvc|cv2):[\s]?(\d{3,4})',
    r'(?:cc|card)(?:num)?[\s:]+(\d{13,16})[\s\n]+(?:exp|expiry|expiration)[\s:]+(\d{1,2})[/|-](\d{2,4})[\s\n]+(?:cvv|cvc|cv2)[\s:]+(\d{3,4})',
    
    # Formats with text between parts
    r'(\d{13,16})(?:\s*(?:card|exp|expiry|expiration)\s*(?:date)?\s*[:|=|-|>])?\s*(\d{1,2})(?:\s*[/|-])?\s*(\d{2,4})(?:\s*(?:cvv|cvc|cv2)\s*[:|=|-|>])?\s*(\d{3,4})',
    
    # Format with label and name (like Jota: with card details)
    r'(?:.*?:)?\s*(\d{13,16})\s*(?:\n|\r\n|\r)(?:.*?)?(\d{1,2})[/|-](\d{2}|20\d{2})(?:\n|\r\n|\r)(\d{3,4})(?:.*)',
    
    # Format with pipe separator and additional details (like wow:)
    r'(?:.*?:)?\s*(\d{13,16})\|(\d{1,2})\|(\d{2})\|(\d{3,4})(?:\|.*)?',
    
    # Format with NR, Holder, CVV, EXPIRE labels (like TA RA:)
    r'(?:.*?)NR:?\s*(\d{13,16})(?:.*?)EXPIRE:?\s*(\d{1,2})[/|-](\d{2}|20\d{2})(?:.*?)CVV:?\s*(\d{3,4})(?:.*)',
    r'(?:.*?)CVV:?\s*(\d{3,4})(?:.*?)EXPIRE:?\s*(\d{1,2})[/|-](\d{2}|20\d{2})(?:.*?)NR:?\s*(\d{13,16})(?:.*)',
    
    # Universal catch-all pattern (more aggressive, use with caution)
    r'(?:.*?)(\d{13,16})(?:.*?)(\d{1,2})[/|-](\d{2}|20\d{2})(?:.*?)(\d{3,4})(?:.*)',
]

# Format CC to desired format
def format_cc(match):  
    # Depending on the pattern, we might need to rearrange the groups
    groups = match.groups()
    
    # Standard pattern should be cc, mm, yy, cvv
    if len(groups) == 4:
        # Check if we have NR: pattern where CVV comes before expiry
        # This means groups would be [cc, cvv, mm, yy] instead of [cc, mm, yy, cvv]
        # We can detect this if the third group (expected to be year) has 3-4 digits (which would be CVV)
        if len(groups[2]) >= 3 and len(groups[2]) <= 4 and len(groups[3]) == 2:
            # Reorder from [cc, cvv, mm, yy] to [cc, mm, yy, cvv]
            cc, cvv, mm, yy = groups
        else:
            cc, mm, yy, cvv = groups
    else:
        # If we don't have exactly 4 groups, something went wrong
        # Return empty to skip this match
        return None
    
    # Clean up and format
    cc = cc.strip()
    mm = mm.strip().zfill(2)  # Ensure month is 2 digits
    
    # Convert YYYY to YY if needed
    yy = yy.strip()
    if len(yy) == 4:
        yy = yy[-2:]
    
    cvv = cvv.strip()
    
    # Basic validation
    if not (13 <= len(cc) <= 19) or not (3 <= len(cvv) <= 4):
        return None
        
    # Create the formatted CC string
    return f"{cc}|{mm}|{yy}|{cvv}"

# Define sources handler
def get_sources():
    sources = []
    if source_groups:
        sources.extend(source_groups)
    if source_channels:
        sources.extend(source_channels)
    return sources

# Scraper Event Handler
@client.on(events.NewMessage(chats=get_sources() if get_sources() else None))  
async def cc_scraper(event):  
    text = event.raw_text  
    found_ccs = set()  
  
    for pattern in cc_patterns:  
        for match in re.finditer(pattern, text):  
            formatted_cc = format_cc(match)
            if formatted_cc:  # Only add valid formatted CCs
                found_ccs.add(formatted_cc)
  
    if found_ccs:  
        for cc in found_ccs:  
            message = f"CC: <code>{cc}</code>"
            
            # Send the message to all target channels
            if target_channels:
                for channel_id in target_channels:
                    try:
                        await client.send_message(channel_id, message, parse_mode="HTML")
                    except Exception as e:
                        print(f"Error sending to channel {channel_id}: {str(e)}")
            else:
                # If no target channels are specified, just print to console
                print(f"Found CC: {cc}")
  
# Run Client  
async def main():  
    await client.start()  
    print("✅ CC Scraper Running...")
    
    # Check and display monitoring status
    sources = get_sources()
    if sources:
        print(f"✅ Monitoring {len(sources)} source(s)")
    else:
        print("⚠️ No sources specified. Will monitor all chats the account has access to.")
    
    if target_channels:
        print(f"✅ Found CCs will be sent to {len(target_channels)} channel(s)")
    else:
        print("⚠️ No target channels specified. Found CCs will be printed to console only.")
        
    await client.run_until_disconnected()  
  
if __name__ == "__main__":  
    asyncio.run(main())