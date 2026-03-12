@"
import groq, os
c = groq.Groq(api_key=os.environ.get('GROQ_API_KEY',''))
r = c.chat.completions.create(model='llama-3.1-8b-instant', messages=[{'role':'user','content':'di hola'}], max_tokens=10)
content = r.choices[0].message.content
print('TIPO:', type(content).__name__)
print('VALOR:', repr(content))
"@ | Out-File -FilePath test_groq.py -Encoding utf8
$env:GROQ_API_KEY = "TU_KEY_REAL_AQUI"
python test_groq.py
