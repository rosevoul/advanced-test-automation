import numpy as np
from orangecontrib.associate.fpgrowth import *
from sklearn.metrics.pairwise import cosine_similarity
from gensim import corpora, models, similarities


def similarity_vector(sent, model):
    # Add the metrics' vectors to one vector; this is the similarity vector
    sent_vectors = np.empty((0, 200), dtype="float32")
    for word in sent:
        word_vector = model[word]
        sent_vectors = np.append(sent_vectors, np.array([word_vector]), axis=0)

    mean_vector = np.mean(sent_vectors, axis=0)
    std_vector = np.std(sent_vectors, axis=0)
    max_vector = np.max(sent_vectors, axis=0)
    min_vector = np.min(sent_vectors, axis=0)

    similarity_vector = np.concatenate(
        [mean_vector, std_vector, max_vector, min_vector])

    return similarity_vector


def average_similarities(model, query, sentences):
    sims = []
    query = [w for w in query if w in model.wv.vocab]
    query_unknown_words = [w for w in query if w not in model.wv.vocab]
    if query_unknown_words:
        print("QUERY: Not in model vocab: ", query_unknown_words)
    for i, sent in enumerate(sentences):
        if sent and query:
            sent = [w for w in sent if w in model.wv.vocab]
            not_in_vocab = [w for w in sent if w not in model.wv.vocab]
            if not_in_vocab:
                print("Not in vocab: ", not_in_vocab)
            sims.append((i, model.n_similarity(query, sent)))
        elif not sent and not query:
            sims.append((i, 1.0))
        else:
            sims.append((i, 0.0))

    return [(i, normalize(s)) for (i, s) in sims]


def statistics_similarities(model, query, sentences):
    sims = []
    query = [w for w in query if w in model.wv.vocab]
    query_unknown_words = [w for w in query if w not in model.wv.vocab]
    if query_unknown_words:
        print("QUERY: Not in model vocab: ", query_unknown_words)
    query_vector = similarity_vector(query, model)

    for i, sent in enumerate(sentences):
        if sent and query:
            sent = [w for w in sent if w in model.wv.vocab]
            not_in_vocab = [w for w in sent if w not in model.wv.vocab]
            if not_in_vocab:
                print("Not in vocab: ", not_in_vocab)
            sent_vector = similarity_vector(sent, model)
            statistics_similarity = cosine_similarity(
                [query_vector], [sent_vector])[0][0]
            sims.append((i, statistics_similarity))
        elif not sent and not query:
            sims.append((i, 1.0))
        else:
            sims.append((i, 0.0))

    return [(i, normalize(s)) for (i, s) in sims]


def weighted_average_vector(sent, tfidf_scores, model):
    sent_vectors = np.empty((200, ), dtype="float32")
    for i, word in enumerate(sent):
        word_vector = model[word]
        tfidf_score = tfidf_scores[i][1]
        sent_vectors = np.append(sent_vectors, np.array(
            np.multiply(tfidf_score, word_vector)), axis=0)

    mean_vector = np.mean(sent_vectors, axis=0)

    return mean_vector


def weighted_average_similarities(model, query, sentences):
    sims = []
    query = [w for w in query if w in model.wv.vocab]
    query_unknown_words = [w for w in query if w not in model.wv.vocab]
    if query_unknown_words:
        print("QUERY: Not in model vocab: ", query_unknown_words)

    tfidf_scores = calculate_tfidf_scores(query, sentences)
    query_vector = weighted_average_vector(query, tfidf_scores, model)

    for i, sent in enumerate(sentences):
        if sent and query:
            sent = [w for w in sent if w in model.wv.vocab]
            not_in_vocab = [w for w in sent if w not in model.wv.vocab]
            if not_in_vocab:
                print("Not in vocab: ", not_in_vocab)
            sent_vector = weighted_average_vector(sent, tfidf_scores, model)
            statistics_similarity = cosine_similarity(
                [query_vector], [sent_vector])[0][0]
            sims.append((i, statistics_similarity))
        elif not sent and not query:
            sims.append((i, 1.0))
        else:
            sims.append((i, 0.0))

    return sims


def calculate_tfidf_scores(query, sentences):
    dictionary = corpora.Dictionary(sentences)
    query_vec = dictionary.doc2bow(query)
    sent_vectors = [dictionary.doc2bow(sent) for sent in sentences]
    tfidf = models.TfidfModel(sent_vectors)

    return tfidf[query_vec]


def tfidf_similarities(query, sentences):
    dictionary = corpora.Dictionary(sentences)
    query_vec = dictionary.doc2bow(query)
    sent_vectors = [dictionary.doc2bow(sent) for sent in sentences]
    tfidf = models.TfidfModel(sent_vectors)
    index = similarities.SparseMatrixSimilarity(
        tfidf[sent_vectors], num_features=len(dictionary.token2id))
    sims = index[tfidf[query_vec]]

    return list(enumerate(sims))


def lsi_similarities(query, sentences):
    # initialize an LSI transformation
    # transform corpus to LSI space and index it

    dictionary = corpora.Dictionary(sentences)
    query_vec = dictionary.doc2bow(query)
    sent_vectors = [dictionary.doc2bow(sent) for sent in sentences]
    lsi = models.LsiModel(sent_vectors, id2word=dictionary, num_topics=100)

    index = similarities.MatrixSimilarity(lsi[sent_vectors])
    sims = index[lsi[query_vec]]

    return [(i, normalize(s)) for (i, s) in list(enumerate(sims))]


def normalize(cosine_similarity):

    return (cosine_similarity + 1) / 2


def jaccard_similarities(query, sentences):
    sims = []
    for i, sent in enumerate(sentences):
        intersection = set(query).intersection(set(sent))
        union = set(query).union(set(sent))
        jaccard_similarity = len(intersection) / len(union)
        sims.append((i, jaccard_similarity))

    return sims


def parameter_similarities(dplist, plists):
    """Calculate similaries based on parameters

    dplist: list of parameters extracted from description
    plists: lists of parameters; each list corresponds to each test block

    :return: list of similarities
    :rtype: list of floats in the range [0, 1]
    """
    sims = []
    for i, plist in enumerate(plists):
        if not dplist and not plist:
            score = 1
        elif not dplist and plist:
            score = 0.0
        elif dplist and not plist:
            score = 0.0
        else:
            ptuples = []
            for paramA in plist:
                for paramB in dplist:
                    if paramA == paramB:
                        pscore = 1
                    else:
                        pscore = 0
                    ptuples.append((paramA, paramB, pscore))
            pscore_sum = 0
            for ptuple in ptuples:
                if ptuple[2]:
                    pscore_sum += 1

            score = pscore_sum / len(dplist)
        sims.append((i, score))

    return sims


def score_associated_blocks(itemsets, previous_blocks, test_blocks_indices, min_confidence=0.3):
    # Create rules and calculate confidence

    confidence_scores = []
    for block in test_blocks_indices:
        rule_set_list = previous_blocks[:]
        rule_set_list.append(block)
        rule_set = frozenset({block for block in rule_set_list})

        if rule_set not in itemsets:
            confidence_scores.append(0.0)
        else:
            result = list(association_rules(
                itemsets, min_confidence, frozenset(rule_set)))
            if result:
                for itemset in result:
                    if itemset[1] == frozenset({block}):
                        confidence_scores.append(itemset[-1])
                    else:
                        confidence_scores.append(0.0)
            else:
                confidence_scores.append(0.0)

    return confidence_scores


def assign_scores(N, k_sims, k_weight, p_sims, p_weight, conf_scores=None, c_weight=0, threshold=0.0):

    blocks_number = len(k_sims)
    scores = []
    top_N_scores_indices = []

    for i in range(blocks_number):
        score = (k_sims[i][1] * k_weight + p_sims[i][1] * p_weight)
        scores.append((i, score))

    sorted_scores = sorted(scores, key=lambda item: item[1], reverse=True)
    for i in range(N):
        if sorted_scores[i][1] >= threshold:
            top_N_scores_indices.append(sorted_scores[i][0])

    return top_N_scores_indices, sorted_scores


def re_rank(top_N_scores_indices, conf_scores, N=20):
    top_conf_scores = []
    new_top_N_scores_indices = []
    for i in top_N_scores_indices:
        top_conf_scores.append((i, conf_scores[i]))

    sorted_scores = sorted(
        top_conf_scores, key=lambda item: item[1], reverse=True)
    print(sorted_scores)
    for i in range(N):
        new_top_N_scores_indices.append(sorted_scores[i][0])

    return new_top_N_scores_indices, sorted_scores


def assign_new_scores(N, k_sims, k_weight, p_sims, p_weight, conf_scores=None, c_weight=0, threshold=0.0):

    blocks_number = len(k_sims)
    initial_scores = []
    new_scores = []
    top_N_scores_indices = []

    for i in range(blocks_number):
        initial_score = (k_sims[i][1] * k_weight + p_sims[i][1] * p_weight)
        initial_scores.append(initial_score)

    for i in range(blocks_number):
        if conf_scores:
            feedback_score = (
                max(initial_scores) - initial_scores[i]) * (conf_scores[i]) + initial_scores[i]
            new_score = feedback_score

        else:
            new_score = initial_scores[i]

        new_scores.append((i, new_score))

    sorted_scores = sorted(new_scores, key=lambda item: item[1], reverse=True)
    for i in range(N):
        if sorted_scores[i][1] >= threshold:
            top_N_scores_indices.append(sorted_scores[i][0])

    return top_N_scores_indices, sorted_scores


def compute_similarities(query, corpora, method, model=None):
    sims = []
    if method == "avg" and model:
        sims = average_similarities(model, query, corpora)
    if method == "wavg" and model:
        sims = weighted_average_similarities(model, query, corpora)
    elif method == "sta" and model:
        sims = statistics_similarities(model, query, corpora)
    elif method == "tf-idf":
        sims = tfidf_similarities(query, corpora)
    elif method == "jac":
        sims = jaccard_similarities(query, corpora)
    elif method == "lsi":
        sims = lsi_similarities(query, corpora)

    return sims


def most_similar_text(query, corpora, model, N, method, threshold=0.0):
    # Return the index of the block description that is matching the highest
    # similarity
    sims = compute_similarities(query, corpora, method, model)
    top_N_similarity_indices = []

    top_similarity_index = max(sims, key=lambda item: item[1])[0]
    most_similar_block = corpora[top_similarity_index]

    sorted_sims = sorted(sims, key=lambda item: item[1], reverse=True)
    for i in range(N):
        if sorted_sims[i][1] >= threshold:
            top_N_similarity_indices.append(sorted_sims[i][0])

    return top_N_similarity_indices, sorted_sims
