## chunk_documents(documents): cutting the text

## It builds a RecursiveCharacterTextSplitter that makes chunks of about 700 characters with 100 characters of overlap. It tries to split on paragraph breaks first, then lines, then spaces, then individual characters, so cuts land on natural boundaries when possible.

## Then it loops over each input document (a dict with text, pokemon, heading, path):

## skips documents with empty text
## splits the text into pieces
## makes one new dict per piece, copying pokemon, heading and path along so every chunk remembers where it came from