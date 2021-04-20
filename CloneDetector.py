import re
import Mapping
import Util
import DataFlowApproach
import Config

def detectClone(codeBlocks):
    for codeBlockId in codeBlocks:
        codeBlock = codeBlocks[codeBlockId]
        code = codeBlock['Code']
        dict_tokens, dict_variables, dict_methods = getAllTokens(code)
        variables_lst = Util.getMostFrequent(
            dict_variables, Config.variableAndMethodsThreshold)
        methods_lst = Util.getMostFrequent(
            dict_methods, Config.variableAndMethodsThreshold)

        variable_scope, method_calls_scope = DataFlowApproach.dataFlowGenerator(
        code, variables_lst, methods_lst)

        codeBlock.update({"Tokens": dict_tokens})
        codeBlock.update({"Variables_Scope": variable_scope})
        codeBlock.update({"Method_Calls_Scope": method_calls_scope})

    for codeBlockId in codeBlocks:
        codeBlock = codeBlocks[codeBlockId]

        tokens = codeBlock["Tokens"]
        variable_scope = codeBlock["Variables_Scope"]
        method_calls_scope = codeBlock["Method_Calls_Scope"]

        codeCloneIds = []

        for codeCandidateId in codeBlocks:
            if codeCandidateId == codeBlockId:
                continue

            simTokens = similarity(
                tokens, codeBlocks[codeCandidateId]["Tokens"])
            if simTokens >= Config.tokenSimilarityThreshold:
                # We will check the control flow of variables here
                codeCandidateBlock = codeBlocks[codeCandidateId]
                candidate_variable_scope = codeCandidateBlock["Variables_Scope"]
                candidate_method_calls_scope = codeCandidateBlock["Method_Calls_Scope"]
                variableSimilarityByDataFlow, methodCallSimilarityByDataFlow = DataFlowApproach.getSimilarity(
                    variable_scope, method_calls_scope, candidate_variable_scope, candidate_method_calls_scope)
                if variableSimilarityByDataFlow >= Config.similarityDataFlowThreshold and methodCallSimilarityByDataFlow >= Config.similarityDataFlowThreshold:
                    codeCloneIds.append(
                        {"Similarity": [simTokens, variableSimilarityByDataFlow, methodCallSimilarityByDataFlow], "codeCandidateId": codeCandidateId})

        codeBlock.update({"CodeClones": codeCloneIds})
    return codeBlocks


def getAllTokens(code):
    list_methods = []
    list_tokens = []
    list_variables = []
    for line in code:
        line = re.sub(r"(\".*?\"|\'.*?\')", " STRING_LITERAL ", line)
        regexPattern = '|'.join(map(re.escape, Mapping.delimiters))
        list_line = re.sub('(?<=\W|\w)(' + regexPattern + ')',
                           r' \1 ', line).split()
        list_line = [unit.strip() for unit in list_line if unit.strip() != ""]
        # print(list_line)

        for idx in range(len(list_line)):
            unit = list_line[idx].strip()
            unit = re.sub(r"^[+-]?((\d+(\.\d+)?)|(\.\d+))$",
                          "INTEGER_LITERAL", unit)
            if unit in Mapping.symbols:
                continue
            elif unit in Mapping.keywords.keys():
                list_tokens.append(Mapping.keywords[unit])
            else:
                if idx + 1 < len(list_line) and list_line[idx + 1].strip() == '(':

                    list_methodName = unit.split(".")

                    list_methods.append(list_methodName[-1])

                    list_tokens.append(list_methodName[-1])
                    # list_tokens.append("TOKEN_METHOD")

                else:
                    list_variableName = unit.split('.')

                    list_variables.append(list_variableName[-1])
                    list_tokens.append("TOKEN_VARIABLE")

    dict_tokens = Util.getFrequencyFromList(list_tokens)
    dict_variables = Util.getFrequencyFromList(list_variables)
    dict_methods = Util.getFrequencyFromList(list_methods)

    return dict_tokens, dict_variables, dict_methods


def similarity(Tokens1, Tokens2):
    """
    input : two list of code
    output : similarity between two list of tokens(decimal between 0 and 1)
    """
    tokensIntersect = 0
    tokens1 = 0
    tokens2 = 0
    tokensUnion = 0
    Tokens1Keys = Tokens1.keys()
    Tokens2Keys = Tokens2.keys()
    for key in Tokens1Keys:
        if key in Tokens2Keys:
            tokensIntersect += min(Tokens1[key], Tokens2[key])
    for key in Tokens1Keys:
        tokens1 += Tokens1[key]
    for key in Tokens2Keys:
        tokens2 += Tokens2[key]
    return (tokensIntersect)/(tokens1 + tokens2 - tokensIntersect)
