def remove_duplicatechar(wordlist):
    deleted_words = 0
    words_to_delete = []
    for word in wordlist:
        check = set()
        for char in word:
            check.add(char)
        if( len(check) != 5 ):
            words_to_delete.append(word)
            deleted_words += 1

    return [word for word in wordlist if word not in words_to_delete], deleted_words
        
def generate_weightmap(wordlist):
    charweights = {}
    totalchar = 5*len(wordlist)
    for word in wordlist:
        for char in word:
            if char not in charweights:
                charweights[ char ] = 0.0
            charweights[ char ] += 1
    
    for char in charweights:
        charweights[ char ] = 1 + (charweights[ char ]/totalchar)

    return charweights

def generate_primewieghts(wordlist, charweights):
    primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101]
    charlist = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

    for i in range(len(charlist)):
        for j in range(i+1, len(charlist)):
            if charweights[ charlist[j] ] > charweights[ charlist[i] ]:
                charlist[i], charlist[j] = charlist[j], charlist[i]

    charToPrime = {}
    for index in range(len(primes)):
        charToPrime[ charlist[index] ] = primes[index]

    wordToHash = {}
    wordToValue = {}

    for word in wordlist:
        hash = 1
        value = 0
        for char in word:
            value += charweights[char]
            hash *= charToPrime[char]
        wordToHash[ word ] = hash
        wordToValue[ word ] = value
    
    return wordToValue, wordToHash, charToPrime

def isUnique(word1, word2, wordToHash):
    x = fractions.Fraction( wordToHash[word1], wordToHash[word2] )
    return x.numerator == wordToHash[word1]
