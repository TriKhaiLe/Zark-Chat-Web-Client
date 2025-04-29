''''
Tạo data NER nhãn BIO cho EVENT, TIME, DURATION
1. Khởi tạo danh sách từ EVENT, TIME, DURATION (có thể có từ gồm nhiều chữ) và template câu mẫu

2. Chọn template ngẫu nhiên, Ví dụ Template được chọn là "[TIME] [EVENT] trong vòng [DURATION]".

3. Thay thế các từ khóa trong template bằng các giá trị ngẫu nhiên từ danh sách đã khởi tạo ở bước 1.

4. Sử dụng word tokenizer (underthesea) để tách câu thành các token.

5. Đối chiếu với template để gán nhãn BIO cho các token sau khi tách:


-- Cach khac
việc làm này có vẻ quá phức tạp, tôi nghĩ tôi sẽ tiếp cận theo hướng khác:
đầu tiên tôi muốn có một đoạn code nhận vào danh sách X các ứng cử viên cho các placeholder (`[TIME]`, `[EVENT]`, `[DURATION]`) và các template câu (vd [TIME] [EVENT] trong vòng [DURATION]). sau đó nó sẽ tokenize từng từ trong danh sách X này và lưu vào danh sách Y mới. Mỗi loại nhãn có thể nằm trong các danh sách Y-TIME, Y-EVENT... riêng.

sau đó cần một đoạn code để tạo một map Z (hoặc cấu trúc gì đó tối ưu, tương tự) cho tất cả danh sách Y đó, trong đó key là các từ đã được tokenize trong danh sách Y mới, value là nhãn của nó (chú ý xử lý case nếu từ nhiều chữ thì nhãn B cho chữ đầu, I cho các chữ sau, và căn cứ vào loại danh sách (time, event...) để biết đó là nhãn nào). ví dụ: sau khi tokenize "thứ 2" vẫn là "thứ 2", map["thứ 2"] = "B-TIME I-TIME".

tiếp theo, tiến hành điền vào placeholder của template bằng danh sách Y. tôi cũng cần cấu trúc như map để lưu các cặp giá trị sau: key: template đã được điền, value: nhãn ứng với từng token trong template (thực hiện bằng cách thay các placeholder bằng nhãn của nó dựa trên map Z, từ nào ko có trong Z thì nhãn O). Sau khi xong bước này, ta có các câu và nhãn cho các token tương ứng trong câu.

Cuối cùng, thực hiện trình bày nó dưới format cũ.

'''

# test_modules.py
# Simple tests that print outputs for each module to verify functionality on Google Colab
# from word_lists import CANDIDATES, TEMPLATES
# from tokenizer import tokenize_candidates
# from label_mapper import create_label_map
# from sentence_generator import generate_sentences
# from data_formatter import save_ner_data

# word_lists.py
# Defines candidate lists for placeholders and sentence templates

CANDIDATES = {
    "TIME": [
        "sáng", "chiều", "tối", "7h", "8h", "9h", "10h", "12h", "15h", "ngày mai",
        "thứ 2", "thứ 3", "thứ 4", "thứ 5", "thứ 6", "thứ 7", "chủ nhật", "tuần sau"
    ],
    "EVENT": [
        "họp", "ăn trưa", "gặp", "đi chơi", "gọi", "tập gym", "dã ngoại", "xem phim",
        "tham gia hội thảo", "làm việc", "giao lưu"
    ],
    "DURATION": [
        "30p", "1 tiếng", "2 tiếng", "90p", "nửa tiếng", "1 giờ", "2 giờ"
    ]
}

TEMPLATES = [
    "[TIME] [EVENT] trong vòng [DURATION]",
    "Hẹn [EVENT] vào [TIME]",
    "[EVENT] [TIME]",
    "Nhắc tôi [EVENT] [TIME]",
    "Đặt lịch [EVENT] [TIME]"
]

# tokenizer.py
# Tokenizes candidate phrases and stores them in Y lists
from underthesea import word_tokenize

def tokenize_candidates(candidates):
    """Tokenize candidate phrases into Y lists for each type."""
    Y_TIME = []
    Y_EVENT = []
    Y_DURATION = []
    
    # Tokenize TIME candidates
    for phrase in candidates["TIME"]:
        tokens = word_tokenize(phrase)
        Y_TIME.append(tokens)
    
    # Tokenize EVENT candidates
    for phrase in candidates["EVENT"]:
        tokens = word_tokenize(phrase)
        Y_EVENT.append(tokens)
    
    # Tokenize DURATION candidates
    for phrase in candidates["DURATION"]:
        tokens = word_tokenize(phrase)
        Y_DURATION.append(tokens)
    
    return {
        "TIME": Y_TIME,
        "EVENT": Y_EVENT,
        "DURATION": Y_DURATION
    }

# label_mapper.py
# Creates a map Z from tokens to their NER labels

def create_label_map(y_lists):
    """Create a map Z: token -> label (B-, I- based on type)."""
    Z = {}
    
    # Process TIME tokens
    for tokens in y_lists["TIME"]:
        if len(tokens) == 1:
            Z[tokens[0]] = "B-TIME"
        else:
            Z[tokens[0]] = "B-TIME"
            for token in tokens[1:]:
                Z[token] = "I-TIME"
    
    # Process EVENT tokens
    for tokens in y_lists["EVENT"]:
        if len(tokens) == 1:
            Z[tokens[0]] = "B-EVENT"
        else:
            Z[tokens[0]] = "B-EVENT"
            for token in tokens[1:]:
                Z[token] = "I-EVENT"
    
    # Process DURATION tokens
    for tokens in y_lists["DURATION"]:
        if len(tokens) == 1:
            Z[tokens[0]] = "B-DURATION"
        else:
            Z[tokens[0]] = "B-DURATION"
            for token in tokens[1:]:
                Z[token] = "I-DURATION"
    
    return Z

# sentence_generator.py
# Fills templates with candidates and maps sentences to token labels
import random

def generate_sentences(templates, y_lists, label_map, num_sentences):
    """Generate sentences and map them to token labels."""
    sentence_label_map = {}
    
    for _ in range(num_sentences):
        # Choose a random template
        template = random.choice(templates)
        
        # Get template placeholders
        placeholders = [p for p in ["TIME", "EVENT", "DURATION"] if f"[{p}]" in template]
        
        # Choose random candidates for each placeholder
        selected_phrases = {}
        for p in placeholders:
            selected_tokens = random.choice(y_lists[p])
            selected_phrases[p] = " ".join(selected_tokens)
        
        # Fill template
        sentence = template
        for p in placeholders:
            sentence = sentence.replace(f"[{p}]", selected_phrases[p], 1)
        
        # Tokenize the sentence
        tokens = word_tokenize(sentence)
        
        # Assign labels using label_map
        labels = []
        template_parts = template.split()
        token_idx = 0
        for part in template_parts:
            if part in ["[TIME]", "[EVENT]", "[DURATION]"]:
                # Get the phrase used for this placeholder
                phrase = selected_phrases[part[1:-1]]
                phrase_tokens = word_tokenize(phrase)
                for _ in phrase_tokens:
                    if token_idx < len(tokens):
                        labels.append(label_map.get(tokens[token_idx], "O"))
                        token_idx += 1
            else:
                # Fixed words (e.g., "trong", "vào")
                fixed_tokens = word_tokenize(part)
                for _ in fixed_tokens:
                    if token_idx < len(tokens):
                        labels.append("O")
                        token_idx += 1
        
        # Ensure labels match tokens
        while len(labels) < len(tokens):
            labels.append("O")
        
        sentence_label_map[sentence] = {"tokens": tokens, "labels": labels}
    
    return sentence_label_map

# data_formatter.py
# Saves sentences and labels to a file in the required format

def save_ner_data(sentence_label_map, output_file):
    """Save sentences and their token labels to a file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        for sentence, data in sentence_label_map.items():
            tokens = data["tokens"]
            labels = data["labels"]
            for token, label in zip(tokens, labels):
                f.write(f"{token} {label}\n")
            f.write("[END]\n")

            
def test_tokenize_candidates():
    print("\n=== Test tokenize_candidates ===")
    # Use a small subset of candidates for clarity
    sample_candidates = {
        "TIME": ["thứ 2", "sáng"],
        "EVENT": ["ăn trưa", "họp"],
        "DURATION": ["2 tiếng", "30p"]
    }

    y_lists = tokenize_candidates(sample_candidates)
    print("Y_TIME:", y_lists["TIME"])
    print("Y_EVENT:", y_lists["EVENT"])
    print("Y_DURATION:", y_lists["DURATION"])

def test_create_label_map():
    print("\n=== Test create_label_map ===")
    # Use output from tokenize_candidates
    y_lists = {
        "TIME": [["thứ", "2"], ["sáng"]],
        "EVENT": [["ăn", "trưa"], ["họp"]],
        "DURATION": [["2", "tiếng"], ["30p"]]
    }
    Z = create_label_map(y_lists)
    print("Label Map Z:", Z)

def test_generate_sentences():
    print("\n=== Test generate_sentences ===")
    # Use small y_lists and a single template
    y_lists = {
        "TIME": [["thứ", "2"], ["sáng"]],
        "EVENT": [["ăn", "trưa"], ["họp"]],
        "DURATION": [["2", "tiếng"], ["30p"]]
    }
    Z = create_label_map(y_lists)
    templates = ["[TIME] [EVENT] trong vòng [DURATION]"]
    sentence_label_map = generate_sentences(templates, y_lists, Z, 2)  # Generate 2 sentences
    for sentence, data in sentence_label_map.items():
        print(f"Sentence: {sentence}")
        print(f"Tokens: {data['tokens']}")
        print(f"Labels: {data['labels']}")
        print("---")

def test_save_ner_data():
    print("\n=== Test save_ner_data ===")
    # Use a single sentence for testing
    sentence_label_map = {
        "thứ 2 họp trong vòng 2 tiếng": {
            "tokens": ["thứ", "2", "họp", "trong", "vòng", "2", "tiếng"],
            "labels": ["B-TIME", "I-TIME", "B-EVENT", "O", "O", "B-DURATION", "I-DURATION"]
        }
    }
    output_file = "test_output.txt"
    save_ner_data(sentence_label_map, output_file)
    print(f"Saved to {output_file}. Content:")
    with open(output_file, 'r', encoding='utf-8') as f:
        print(f.read())

if __name__ == "__main__":
    test_tokenize_candidates()
    # test_create_label_map()
    # test_generate_sentences()
    # test_save_ner_data()












