"""
Given an integer array nums, return all the triplets [nums[i], nums[j], nums[k]] where nums[i] + nums[j] + nums[k] == 0, and the indices i, j and k are all distinct.

The output should not contain any duplicate triplets. You may return the output and the triplets in any order.

Example 1:

Input: nums = [-1,0,1,2,-1,-4]

Output: [[-1,-1,2],[-1,0,1]]
Explanation:
nums[0] + nums[1] + nums[2] = (-1) + 0 + 1 = 0.
nums[1] + nums[2] + nums[4] = 0 + 1 + (-1) = 0.
nums[0] + nums[3] + nums[4] = (-1) + 2 + (-1) = 0.
The distinct triplets are [-1,0,1] and [-1,-1,2].

Example 2:

Input: nums = [0,1,1]

Output: []
Explanation: The only possible triplet does not sum up to 0.

Example 3:

Input: nums = [0,0,0]

Output: [[0,0,0]]
Explanation: The only possible triplet sums up to 0.

Constraints:

3 <= nums.length <= 1000
-10^5 <= nums[i] <= 10^5

"""
'''
try:
    for i in range(19):
        print(i)
except Explanation as e:
    print(str(e))
'''
'''
class Solution:
    def SumTwo(self, nums , target):
        hash_map = {}
        for i , item in enumerate(nums):
            tar  = target - item
            if tar in hash_map:
                return [hash_map[tar] , nums[i]]
            hash_map[item] = i + 1

obj = Solution()
print(obj.SumTwo([2,3,4], 6))
'''
'''
def dublicate(nums):
    hash_set = {}
    for item in nums:
        if item in hash_set:
            hash_set[item] = 1
        else:
            hash_set[item] = 0
    return [item for item in hash_set if hash_set[item]==1]
print(dublicate([4, 3, 2, 7, 8, 2, 3, 1]))
'''
'''
def seen(nums):
    return True if len(set(nums))!=len(nums) else False
print(seen([1,2,3,4]))

'''

'''
def firstunique(nums):
    hash_set = {}
    for item in nums:
        if item in hash_set:
            hash_set[item] = 1
        else:
            hash_set[item] = 0
        return 
print(firstunique([1,2,35,]))


'''

# strs = ["eat","tea","tan","ate","nat","bat"] #input 

# # Output: [["bat"],["nat","tan"],["ate","eat","tea"]]


# class Solution(object):
#     def groupAnagrams(self, strs):
#         for item in strs




class Solution(object):
    def firstUniqChar(self, s):
        hashmap = {}
        for i, ch in enumerate(s):
            if ch in hashmap:
                return ch
            hashmap[ch] = i
        print

obj  = Solution()
print(obj.firstUniqChar('leetcode'))


























