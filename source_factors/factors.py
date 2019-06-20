# *-* encoding: utf-8 *-*

import re

from abc import ABC, abstractmethod
from typing import Dict

class Factor(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def compute(self, segment: str):
        """
        Computes the factor on the tokens in the segment.
        """
        raise NotImplementedError()

    def compute_json(self, 
                     jobj: Dict) -> str:
        field = 'tok_text' if 'tok_text' in jobj else 'raw_text'
        return self.compute(jobj[field])


class SubwordFactor(Factor):
    def __init__(self):
        pass

    def compute_sp(self, sp_str: str) -> str:
        """
        iron cement is a ready for use paste which is laid as a fillet by putty knife or finger in the mould edges ( corners ) of the steel ingot mould .
        ▁iron ▁c ement ▁is ▁a ▁ready ▁for ▁use ▁past e ▁which ▁is ▁laid ▁as ▁a ▁fill et ▁by ▁put ty ▁kni fe ▁or ▁finger ▁in ▁the ▁mould ▁edge s ▁( ▁corner s ▁) ▁of ▁the ▁steel ▁in go t ▁mould ▁.

        The options are:
        O: a complete word
        B: beginning of a multi-token word
        I: interior of a multi-token word
        E: end of a multi-token word
        """

        def process_stack(stack):
            factors_ = []
            if len(stack) == 1:
                factors.append('O')
            elif len(stack) > 1:
                stack[0] = 'B'
                # all interior words are 'I'
                for i in range(1, len(stack) - 1):
                    stack[i] = 'I'
                stack[-1] = 'E'
                factors_ += stack
            return factors_

        factors = []
        tokens = sp_str.split()
        stack = [tokens.pop(0)]
        for i, token in enumerate(tokens):
            if token.startswith('▁'):
                factors += process_stack(stack)
                stack = []
            stack.append(token)

        factors += process_stack(stack)

        return ' '.join(factors)

    def compute_bpe(self, bpe_str: str) -> str:
        """
        Computes NER-style features for a BPE stream. e.g.,

        The boy ate the waff@@ le .
          O   O   O   O      B  E O

        The options are:
        O: a complete word
        B: beginning of a multi-token word
        I: interior of a multi-token word
        E: end of a multi-token word

        :param bpe_str: The BPE string.
        :return: A string of BPE factors.
        """
        factors = []
        was_in_bpe = False
        for i, token in enumerate(bpe_str.split()):
            now_in_bpe = token.endswith('@@')
            if was_in_bpe:
                if now_in_bpe:
                    factor = 'I'
                else:
                    factor = 'E'
            else:
                if now_in_bpe:
                    factor = 'B'
                else:
                    factor = 'O'

            was_in_bpe = now_in_bpe
            factors.append(factor)

        return ' '.join(factors)

    def compute(self, subword_str) -> str:
        """
        Computes features over a subword string.
        Automatically determines whether its SentencePiece or BPE.
        """

        return self.compute_sp(subword_str) if '▁' in subword_str else self.compute_bpe(subword_str)

    def compute_json(self, jobj):
        return self.compute(jobj['subword_text'])


class CaseFactor(Factor):
    def __init__(self):
        pass

    def case(self, token):
        if token.isupper():
            return 'UPPER'
        elif token.istitle():
            return 'Title'
        elif token.islower():
            return 'lower'
        else:
            return '-'

    def compute(self, segment: str) -> str:
        return ' '.join([self.case(token) for token in segment.split()])


class MaskFactor(Factor):
    def __init__(self):
        self.mask_regex = re.compile('__[A-Za-z0-9]+(_\d+)?__')

    def is_mask(self, token: str):
        return 'Y' if self.mask_regex.match(token) else 'n'

    def compute(self, segment: str) -> str:
        return ' '.join([self.is_mask(token) for token in segment.split()])

    def compute_json(self, jobj: Dict) -> str:
        return self.compute(jobj['text'])
        

class NumberFactor(Factor):
    def __init__(self):
        self.regex = re.compile(r'\B-\.\d+|\B\.\d+|\B-\d+(,\d+)*(\.\d+(e-?\d+)?)?|\b\d+(,\d+)*(\.\d+(e-?\d+)?)?')

    def is_number(self, token: str):
        return 'Y' if self.regex.match(token) else 'n'

    def compute(self, segment: str) -> str:
        return ' '.join([self.is_number(token) for token in segment.split()])
        

class URLFactor(Factor):
    def __init__(self):
        self.regex = re.compile(r'(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/|ftp:\/\/)?[A-Za-z0-9]+([\-\.]{1}[A-Za-z0-9]+)*\.(zw|zuerich|zone|zm|zip|zero|zara|zappos|za|yun|yt|youtube|you|yokohama|yoga|yodobashi|ye|yandex|yamaxun|yahoo|yachts|xyz|xxx|xin|xihuan|xfinity|xerox|xbox|wtf|wtc|ws|wow|world|works|work|woodside|wolterskluwer|wme|winners|wine|windows|win|williamhill|wiki|wien|whoswho|wf|weir|weibo|wedding|wed|website|weber|webcam|weatherchannel|weather|watches|watch|warman|wanggou|wang|walter|walmart|wales|vuelos|vu|voyage|voto|voting|vote|volvo|volkswagen|vodka|vn|vlaanderen|vivo|viva|vistaprint|vision|visa|virgin|vip|vin|villas|viking|vig|video|viajes|vi|vg|vet|versicherung|verisign|ventures|vegas|ve|vc|vanguard|vana|vacations|va|uz|uy|us|ups|uol|uno|university|unicom|uk|ug|uconnect|ubs|ubank|ua|tz|tw|tvs|tv|tushu|tunes|tui|tube|tt|trv|trust|travelersinsurance|travelers|travelchannel|travel|training|trading|trade|tr|toys|toyota|town|tours|total|toshiba|toray|top|tools|tokyo|today|to|tn|tmall|tm|tl|tkmaxx|tk|tjx|tjmaxx|tj|tirol|tires|tips|tiffany|tienda|tickets|tiaa|theatre|theater|thd|th|tg|tf|teva|tennis|temasek|telefonica|tel|technology|tech|team|tdk|td|tci|tc|taxi|tax|tattoo|tatar|tatamotors|target|taobao|talk|taipei|tab|sz|systems|symantec|sydney|sy|sx|swiss|swiftcover|swatch|sv|suzuki|surgery|surf|support|supply|supplies|sucks|su|style|study|studio|stream|store|storage|stockholm|stcgroup|stc|statefarm|statebank|starhub|star|staples|stada|st|ss|srt|srl|sr|spreadbetting|spot|sport|space|soy|sony|song|solutions|solar|sohu|software|softbank|social|soccer|so|sncf|sn|smile|smart|sm|sling|sl|skype|sky|skin|ski|sk|sj|site|singles|sina|silk|si|shriram|showtime|show|shouji|shopping|shop|shoes|shiksha|shia|shell|shaw|sharp|shangrila|sh|sg|sfr|sexy|sex|sew|seven|ses|services|sener|select|seek|security|secure|seat|search|se|sd|scot|scor|scjohnson|science|schwarz|schule|school|scholarships|schmidt|schaeffler|scb|sca|sc|sbs|sbi|sb|saxo|save|sas|sarl|sap|sanofi|sandvikcoromant|sandvik|samsung|samsclub|salon|sale|sakura|safety|safe|saarland|sa|ryukyu|rwe|rw|run|ruhr|rugby|ru|rsvp|rs|room|rogers|rodeo|rocks|rocher|ro|rmit|rip|rio|ril|rightathome|ricoh|richardli|rich|rexroth|reviews|review|restaurant|rest|republican|report|repair|rentals|rent|ren|reliance|reit|reisen|reise|rehab|redumbrella|redstone|red|recipes|realty|realtor|realestate|read|re|raid|radio|racing|qvc|quest|quebec|qpon|qa|py|pwc|pw|pub|pt|ps|prudential|pru|protection|property|properties|promo|progressive|prof|productions|prod|pro|prime|press|praxi|pramerica|pr|post|porn|politie|poker|pohl|pnc|pn|pm|plus|plumbing|playstation|play|place|pl|pk|pizza|pioneer|pink|ping|pin|pid|pictures|pictet|pics|piaget|physio|photos|photography|photo|phone|philips|phd|pharmacy|ph|pg|pfizer|pf|pet|pe|pccw|pay|passagens|party|parts|partners|pars|paris|panasonic|page|pa|ovh|ott|otsuka|osaka|origins|organic|org|orange|oracle|open|ooo|onyourside|online|onl|ong|one|omega|om|ollo|oldnavy|olayangroup|olayan|okinawa|office|off|observer|obi|nz|nyc|nu|ntt|nrw|nra|nr|np|nowtv|nowruz|now|norton|northwesternmutual|nokia|no|nl|nissay|nissan|ninja|nikon|nike|nico|ni|nhk|ngo|ng|nfl|nf|nexus|nextdirect|next|news|newholland|new|neustar|network|netflix|netbank|net|nec|ne|nc|nba|navy|natura|nationwide|name|nagoya|nadex|nab|na|mz|my|mx|mw|mv|mutual|museum|mu|mtr|mtn|mt|msd|ms|mr|mq|mp|movistar|movie|mov|motorcycles|moto|moscow|mortgage|mormon|mopar|monster|money|monash|mom|moi|moe|moda|mobily|mobile|mobi|mo|mn|mma|mm|mls|mlb|ml|mk|mitsubishi|mit|mint|mini|mil|microsoft|miami|mh|mg|metlife|merckmsd|menu|men|memorial|meme|melbourne|meet|media|med|me|md|mckinsey|mc|mba|mattel|maserati|marshalls|marriott|markets|marketing|market|map|mango|management|man|makeup|maison|maif|madrid|macys|ma|ly|lv|luxury|luxe|lupin|lundbeck|lu|ltda|ltd|lt|ls|lr|lplfinancial|lpl|love|lotto|lotte|london|lol|loft|locus|locker|loans|loan|llc|lk|lixil|living|live|lipsy|link|linde|lincoln|limo|limited|lilly|like|lighting|lifestyle|lifeinsurance|life|lidl|liaison|li|lgbt|lexus|lego|legal|lefrak|leclerc|lease|lds|lc|lb|lawyer|law|latrobe|latino|lat|lasalle|lanxess|landrover|land|lancome|lancia|lancaster|lamer|lamborghini|ladbrokes|lacaixa|la|kz|kyoto|ky|kw|kuokgroup|kred|krd|kr|kpn|kpmg|kp|kosher|komatsu|koeln|kn|km|kiwi|kitchen|kindle|kinder|kim|kia|ki|kh|kg|kfh|kerryproperties|kerrylogistics|kerryhotels|ke|kddi|kaufen|juniper|juegos|jprs|jpmorgan|jp|joy|jot|joburg|jobs|jo|jnj|jmp|jm|jll|jio|jewelry|jetzt|jeep|je|jcp|jcb|java|jaguar|iveco|itv|itau|it|istanbul|ist|ismaili|iselect|is|irish|ir|iq|ipiranga|io|investments|intuit|international|intel|int|insure|insurance|institute|ink|ing|info|infiniti|industries|inc|in|immobilien|immo|imdb|imamat|im|il|ikano|ifm|ieee|ie|id|icu|ice|icbc|ibm|hyundai|hyatt|hughes|hu|ht|hsbc|hr|how|house|hotmail|hotels|hoteles|hot|hosting|host|hospital|horse|honeywell|honda|homesense|homes|homegoods|homedepot|holiday|holdings|hockey|hn|hm|hkt|hk|hiv|hitachi|hisamitsu|hiphop|hgtv|hermes|here|helsinki|help|healthcare|health|hdfcbank|hdfc|hbo|haus|hangout|hamburg|hair|gy|gw|guru|guitars|guide|guge|gucci|guardian|gu|gt|gs|group|grocery|gripe|green|gratis|graphics|grainger|gr|gq|gp|gov|got|gop|google|goog|goodyear|goo|golf|goldpoint|gold|godaddy|gn|gmx|gmo|gmbh|gmail|gm|globo|global|gle|glass|glade|gl|giving|gives|gifts|gift|gi|gh|ggee|gg|gf|george|genting|gent|gea|ge|gdn|gd|gbiz|gb|garden|gap|games|game|gallup|gallo|gallery|gal|ga|fyi|futbol|furniture|fund|fun|fujixerox|fujitsu|ftr|frontier|frontdoor|frogans|frl|fresenius|free|fr|fox|foundation|forum|forsale|forex|ford|football|foodnetwork|food|foo|fo|fm|fly|flowers|florist|flir|flights|flickr|fk|fj|fitness|fit|fishing|fish|firmdale|firestone|fire|financial|finance|final|film|fido|fidelity|fiat|fi|ferrero|ferrari|feedback|fedex|fast|fashion|farmers|farm|fans|fan|family|faith|fairwinds|fail|fage|extraspace|express|exposed|expert|exchange|everbank|events|eus|eurovision|eu|etisalat|et|esurance|estate|esq|es|erni|ericsson|er|equipment|epson|enterprises|engineering|engineer|energy|emerck|email|eg|ee|education|edu|edeka|eco|ec|eat|earth|dz|dvr|dvag|durban|dupont|duns|dunlop|duck|dubai|dtv|drive|download|dot|domains|doha|dog|dodge|doctor|docs|do|dnp|dm|dk|dj|diy|dish|discover|discount|directory|direct|digital|diet|diamonds|dhl|dev|design|desi|dentist|dental|democrat|delta|deloitte|dell|delivery|degree|deals|dealer|deal|de|dds|dclk|day|datsun|dating|date|data|dance|dad|dabur|cz|cyou|cymru|cy|cx|cw|cv|cuisinella|cu|csc|cruises|cruise|crs|crown|cricket|creditunion|creditcard|credit|cr|courses|coupons|coupon|country|corsica|coop|cool|cookingchannel|cooking|contractors|contact|consulting|construction|condos|comsec|computer|compare|company|community|commbank|comcast|com|cologne|college|coffee|codes|coach|co|cn|cm|clubmed|club|cloud|clothing|clinique|clinic|click|cleaning|claims|cl|ck|cityeats|city|citic|citi|citadel|cisco|circle|cipriani|ci|church|chrysler|chrome|christmas|chintai|cheap|chat|chase|charity|channel|chanel|ch|cg|cfd|cfa|cf|cern|ceo|center|ceb|cd|cc|cbs|cbre|cbn|cba|catholic|catering|cat|casino|cash|caseih|case|casa|cartier|cars|careers|career|care|cards|caravan|car|capitalone|capital|capetown|canon|cancerresearch|camp|camera|cam|calvinklein|call|cal|cafe|cab|ca|bzh|bz|by|bw|bv|buzz|buy|business|builders|build|bugatti|budapest|bt|bs|brussels|brother|broker|broadway|bridgestone|bradesco|br|box|boutique|bot|boston|bostik|bosch|booking|book|boo|bond|bom|bofa|boehringer|boats|bo|bnpparibas|bnl|bn|bmw|bms|bm|blue|bloomberg|blog|blockbuster|blackfriday|black|bj|biz|bio|bingo|bing|bike|bid|bible|bi|bharti|bh|bg|bf|bet|bestbuy|best|berlin|bentley|beer|beauty|beats|be|bd|bcn|bcg|bbva|bbt|bbc|bb|bayern|bauhaus|basketball|baseball|bargains|barefoot|barclays|barclaycard|barcelona|bar|bank|band|bananarepublic|banamex|baidu|baby|ba|azure|az|axa|ax|aws|aw|avianca|autos|auto|author|auspost|audio|audible|audi|auction|au|attorney|athleta|at|associates|asia|asda|as|arte|art|arpa|army|archi|aramco|arab|ar|aquarelle|aq|apple|app|apartments|aol|ao|anz|anquan|android|analytics|amsterdam|amica|amfam|amex|americanfamily|americanexpress|am|alstom|alsace|ally|allstate|allfinanz|alipay|alibaba|alfaromeo|al|akdn|airtel|airforce|airbus|aigo|aig|ai|agency|agakhan|ag|africa|afl|afamilycompany|af|aetna|aero|aeg|ae|adult|ads|adac|ad|actor|aco|accountants|accountant|accenture|academy|ac|abudhabi|abogado|able|abc|abbvie|abbott|abb|abarth|aarp|aaa)(:[0-9]{1,5})?(\/[^\(^\)]*)?')

    def is_url(self, token: str):
        ans = 'Y' if self.regex.match(token) else 'n'
#        print(f'IS_URL({token}) -> {ans}')
        return ans

    def compute(self, segment: str) -> str:
        return ' '.join([self.is_url(token) for token in segment.split()])
        

class EmailFactor(Factor):
    def __init__(self):
        self.regex = re.compile(r'[\w\.\-\+]+\@\w+\.[\w\.]*\w+')

    def is_email(self, token: str):
        return 'Y' if self.regex.match(token) else 'n'

    def compute(self, segment: str) -> str:
        return ' '.join([self.is_email(token) for token in segment.split()])
