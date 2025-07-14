from chatbot import get_exact_answer, save_unanswered_question

# Poser une question
question = input("Pose ta question : ")

# Obtenir une réponse
reponse = get_exact_answer(question)

if reponse:
    print("Chatbot :", reponse)
else:
    print("Chatbot : Désolé, je ne connais pas encore cette réponse.")
    save_unanswered_question(question)
